import anyio
from uuid import uuid4
from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import JSONResponse

import app.routes.analyze as analyze_route
from app.schemas import AnalysisJobAcceptedResponse, AnalysisJobStatusResponse, AnalyzeResponse
from services.analysis_jobs import AnalysisJobRequest, AnalysisJobService, AnalysisQueueFullError
from services.analysis_types import AnalysisMode, normalize_analysis_mode
from services.capture_repository import (
    CaptureRepository,
    CaptureRepositoryError,
    incoming_capture_root,
)
from services.image_preprocess import ImagePreprocessError, preprocess_image
from services.result_logger import log_analysis_run, log_prediction, log_sensor_evidence, save_source_image
from services.sensor_evidence import collect_sensor_evidence
from services.validation import ImageValidationError, validate_upload_file


router = APIRouter()


@router.post("/analysis-jobs", response_model=AnalysisJobAcceptedResponse)
async def create_analysis_job(
    request: Request,
    image: UploadFile = File(...),
    mode: str = Form(default=AnalysisMode.SENSOR_ASSISTED.value),
    save_result: bool = Form(default=True),
    capture_id: str | None = Form(default=None),
    capture_time_ms: int | None = Form(default=None),
    camera_facing_mode: str | None = Form(default=None),
    clock_offset_ms: int | None = Form(default=None),
    clock_rtt_ms: int | None = Form(default=None),
) -> JSONResponse:
    try:
        normalized_mode = normalize_analysis_mode(mode)
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(exc)},
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

    service: AnalysisJobService = request.app.state.analysis_jobs
    try:
        sensor_evidence = None
        sensor_bridge = getattr(request.app.state, "sensor_bridge", None)
        if capture_time_ms is not None and sensor_bridge is not None:
            sensor_evidence = collect_sensor_evidence(
                sensor_bridge,
                capture_id=capture_id,
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
        record = service.enqueue(AnalysisJobRequest(
            image_bytes=upload.data,
            filename=upload.filename,
            content_type=upload.content_type,
            width=processed.width,
            height=processed.height,
            mode=normalized_mode,
            save_result=save_result,
            capture_id=capture_id,
            capture_time_ms=capture_time_ms,
            camera_facing_mode=camera_facing_mode,
            sensor_evidence=sensor_evidence,
        ))
    except AnalysisQueueFullError as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Retry-After": "2"},
            content={"error": str(exc)},
        )

    response = AnalysisJobAcceptedResponse(
        job_id=record.job_id,
        status=record.status,
        poll_url=f"/analysis-jobs/{record.job_id}",
        queue_scope="single_process_non_durable",
    )
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=response.model_dump())


@router.get("/analysis-jobs/{job_id}", response_model=AnalysisJobStatusResponse)
async def get_analysis_job(request: Request, job_id: str) -> JSONResponse:
    service: AnalysisJobService = request.app.state.analysis_jobs
    record = service.get(job_id)
    if record is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Pekerjaan analisis tidak ditemukan atau sudah kedaluwarsa."},
        )
    response = AnalysisJobStatusResponse(
        job_id=record.job_id,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        result=AnalyzeResponse.model_validate(record.result) if record.result is not None else None,
        error=record.error,
    )
    return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())


async def run_analysis_job(job: AnalysisJobRequest) -> dict[str, object]:
    capture_repository = None
    if job.stored_capture_id is not None:
        capture_repository = CaptureRepository(
            incoming_capture_root(analyze_route.settings.results_dir)
        )
    try:
        if capture_repository is not None:
            capture_repository.mark_running(job.stored_capture_id)
        pipeline_result = await analyze_route.analyze_image_bytes(
            job.image_bytes,
            job.filename,
            job.mode,
            analyze_route.settings,
            analyze_route.gemma_client,
            job.sensor_evidence,
        )
        if not pipeline_result.success:
            raise RuntimeError(pipeline_result.error or "Analyze failed.")
        analysis_run_id = uuid4().hex
        source_image = job.source_image
        if job.save_result and analyze_route.settings.save_results and source_image is None:
            source_image = save_source_image(
                analyze_route.settings.results_dir,
                job.image_bytes,
                job.filename,
                analysis_run_id,
            )
        response = AnalyzeResponse(
            success=True,
            analysis_run_id=analysis_run_id,
            filename=job.filename,
            content_type=job.content_type,
            width=job.width,
            height=job.height,
            mode=job.mode,
            gemma_description=pipeline_result.gemma_description,
            gemma_structured=pipeline_result.gemma_structured,
            final_description=pipeline_result.final_description,
            display=pipeline_result.display,
            latency=pipeline_result.latency,
            source_image_url=(source_image or {}).get("url"),
            mock=pipeline_result.mock,
            error=pipeline_result.error,
            sensor_evidence=job.sensor_evidence,
            sensor_contribution=pipeline_result.sensor_contribution,
            analysis_method=pipeline_result.analysis_method,
            gemma_provenance=pipeline_result.gemma_provenance,
        )
        if job.save_result and analyze_route.settings.save_results:
            log_analysis_run(
                analyze_route.settings.results_dir,
                analysis_run_id=analysis_run_id,
                capture_id=job.capture_id,
                filename=job.filename,
                sensor_evidence=job.sensor_evidence,
                outputs={job.mode.value: response.model_dump(mode="json")},
                source_image=source_image,
            )
            log_prediction(analyze_route.settings.results_dir, analyze_route.prediction_row(pipeline_result))
            if job.sensor_evidence is not None:
                log_sensor_evidence(
                    analyze_route.settings.results_dir,
                    image_name=job.filename,
                    mode=job.mode,
                    evidence=job.sensor_evidence,
                )
        if capture_repository is not None:
            capture_repository.mark_completed(
                job.stored_capture_id,
                analysis_run_id=analysis_run_id,
            )
        return response.model_dump()
    except Exception as exc:
        if capture_repository is not None:
            try:
                capture_repository.mark_failed(job.stored_capture_id, error=str(exc))
            except CaptureRepositoryError:
                pass
        raise
