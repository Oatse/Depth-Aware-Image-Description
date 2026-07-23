import anyio
from uuid import uuid4
from fastapi import APIRouter, File, Form, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse

import app.routes.analyze as analyze_route
from app.schemas import (
    AnalysisJobAcceptedResponse,
    CaptureCountResponse,
    CaptureCreatedResponse,
    CaptureListResponse,
)
from services.analysis_jobs import (
    AnalysisJobRequest,
    AnalysisJobService,
    AnalysisJobStatus,
    AnalysisQueueFullError,
)
from services.analysis_types import AnalysisMode, normalize_analysis_mode
from services.capture_repository import (
    CAPTURE_CANDIDATE_BATCH_ID,
    CAPTURE_CANDIDATE_IMAGE_PREFIX,
    CaptureAlreadyExistsError,
    CaptureNotFoundError,
    CaptureRepository,
    CaptureRepositoryError,
    CaptureStateError,
    incoming_capture_root,
)
from services.image_preprocess import ImagePreprocessError, preprocess_image
from services.sensor_evidence import collect_sensor_evidence
from services.validation import ImageValidationError, validate_upload_file


router = APIRouter()


def _repository() -> CaptureRepository:
    return CaptureRepository(incoming_capture_root(analyze_route.settings.results_dir))


@router.post(
    "/captures",
    response_model=CaptureCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_capture(
    request: Request,
    image: UploadFile = File(...),
    capture_id: str | None = Form(default=None),
    capture_time_ms: int = Form(..., ge=0),
    camera_facing_mode: str | None = Form(default=None),
    mode: str = Form(default=AnalysisMode.SENSOR_ASSISTED.value),
    clock_offset_ms: int | None = Form(default=None),
    clock_rtt_ms: int | None = Form(default=None),
    ground_truth_cm: float = Form(..., ge=20, le=200),
    repeat_index: int | None = Form(default=None, ge=1),
) -> CaptureCreatedResponse | JSONResponse:
    try:
        normalized_mode = normalize_analysis_mode(mode)
    except ValueError as exc:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(exc)})
    if ground_truth_cm <= analyze_route.settings.camera_sensor_offset_cm:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "ground_truth_cm harus lebih besar daripada offset kamera-sensor."},
        )
    try:
        upload = await validate_upload_file(image, analyze_route.settings.max_image_size_mb)
        processed = await anyio.to_thread.run_sync(
            preprocess_image,
            upload.data,
            analyze_route.settings.image_max_dimension,
        )
    except (ImageValidationError, ImagePreprocessError) as exc:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(exc)})

    canonical_capture_id = capture_id or uuid4().hex
    sensor_evidence = None
    sensor_bridge = getattr(request.app.state, "sensor_bridge", None)
    if sensor_bridge is not None:
        sensor_evidence = collect_sensor_evidence(
            sensor_bridge,
            capture_id=canonical_capture_id,
            client_capture_time_ms=capture_time_ms,
            camera_facing_mode=camera_facing_mode,
            match_window_ms=analyze_route.settings.sensor_match_window_ms,
            max_clock_skew_ms=analyze_route.settings.sensor_max_clock_skew_ms,
            clock_offset_ms=clock_offset_ms,
            clock_rtt_ms=clock_rtt_ms,
            max_clock_rtt_ms=analyze_route.settings.sensor_clock_rtt_max_ms,
            freshness_max_age_ms=analyze_route.settings.sensor_freshness_max_age_ms,
            pair_disagreement_cm=analyze_route.settings.sensor_pair_disagreement_cm,
        )
        canonical_capture_id = str(sensor_evidence.get("capture_id") or canonical_capture_id)

    evidence = sensor_evidence or {}
    samples = evidence.get("samples") or {}
    sensor_1 = samples.get("sensor_1") or {}
    sensor_2 = samples.get("sensor_2") or {}
    if (
        evidence.get("status") != "paired"
        or sensor_1.get("status") != "ok"
        or sensor_2.get("status") != "ok"
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "Capture kandidat memerlukan dua sensor paired dan berstatus ok."},
        )

    offset = analyze_route.settings.camera_sensor_offset_cm
    metadata = {
        "camera_sensor_offset_cm": offset,
        "ground_truth_cm": ground_truth_cm,
        "sensor_face_ground_truth_cm": ground_truth_cm - offset,
        "repeat_index": repeat_index,
    }
    repository = _repository()
    try:
        record = repository.create(
            image_bytes=upload.data,
            original_filename=upload.filename,
            content_type=upload.content_type,
            width=processed.width,
            height=processed.height,
            capture_id=canonical_capture_id,
            batch_id=CAPTURE_CANDIDATE_BATCH_ID,
            capture_time_ms=capture_time_ms,
            camera_facing_mode=camera_facing_mode,
            mode=normalized_mode.value,
            sensor_evidence=sensor_evidence,
            metadata=metadata,
            image_path_prefix=CAPTURE_CANDIDATE_IMAGE_PREFIX,
        )
    except CaptureAlreadyExistsError as exc:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"error": str(exc)})
    except CaptureRepositoryError as exc:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(exc)})
    return CaptureCreatedResponse(
        capture=record,
        capture_count=repository.count(batch_id=record["batch_id"]),
    )


@router.get("/captures", response_model=CaptureListResponse)
async def list_captures(
    batch_id: str | None = Query(default=None),
    capture_status: str | None = Query(default=None, alias="status"),
) -> CaptureListResponse | JSONResponse:
    try:
        records = _repository().list(batch_id=batch_id, status=capture_status)
    except CaptureRepositoryError as exc:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(exc)})
    return CaptureListResponse(count=len(records), captures=records)


@router.get("/captures/count", response_model=CaptureCountResponse)
async def count_captures(batch_id: str | None = Query(default=None)) -> CaptureCountResponse | JSONResponse:
    try:
        count = _repository().count(batch_id=batch_id)
    except CaptureRepositoryError as exc:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(exc)})
    return CaptureCountResponse(count=count, batch_id=batch_id)


@router.post(
    "/captures/{capture_id}/analysis-jobs",
    response_model=AnalysisJobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_capture_analysis_job(
    request: Request,
    capture_id: str,
    mode: str | None = Form(default=None),
    reanalyze: bool = Query(default=False),
) -> AnalysisJobAcceptedResponse | JSONResponse:
    repository = _repository()
    try:
        capture = repository.get(capture_id)
        normalized_mode = normalize_analysis_mode(mode or str(capture.get("mode") or "sensor_assisted"))
        image_bytes = repository.read_image(capture_id)
    except CaptureNotFoundError as exc:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": str(exc)})
    except (CaptureRepositoryError, ValueError) as exc:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": str(exc)})

    service: AnalysisJobService = request.app.state.analysis_jobs
    if capture.get("status") in {"queued", "running"}:
        active_job_id = str(capture.get("analysis_job_id") or "")
        active_job = service.get(active_job_id) if active_job_id else None
        if active_job is not None and active_job.status in {
            AnalysisJobStatus.QUEUED,
            AnalysisJobStatus.RUNNING,
        }:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"error": f"Capture {capture_id} sedang dianalisis oleh job {active_job_id}."},
            )
        try:
            repository.recover_orphaned_analysis(capture_id)
        except CaptureStateError as exc:
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"error": str(exc)})
    image = capture["image"]
    job_id = uuid4().hex
    try:
        repository.mark_queued(capture_id, job_id=job_id, mode=normalized_mode.value, allow_completed=reanalyze)
        job = service.enqueue(
            AnalysisJobRequest(
                image_bytes=image_bytes,
                filename=str(image["original_filename"]),
                content_type=str(image["content_type"]),
                width=int(image["width"]),
                height=int(image["height"]),
                mode=normalized_mode,
                save_result=True,
                capture_id=capture_id,
                capture_time_ms=int(capture["capture_time_ms"]),
                camera_facing_mode=capture.get("camera_facing_mode"),
                sensor_evidence=capture.get("sensor_evidence"),
                stored_capture_id=capture_id,
                source_image=repository.public_source_image(capture_id),
            ),
            job_id=job_id,
        )
    except CaptureStateError as exc:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"error": str(exc)})
    except AnalysisQueueFullError as exc:
        repository.mark_failed(capture_id, error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Retry-After": "2"},
            content={"error": str(exc)},
        )
    return AnalysisJobAcceptedResponse(
        job_id=job.job_id,
        status=job.status,
        poll_url=f"/analysis-jobs/{job.job_id}",
        queue_scope="single_process_non_durable",
    )
