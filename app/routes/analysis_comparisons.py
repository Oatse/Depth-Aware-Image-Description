import anyio
from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import JSONResponse

import app.routes.analyze as analyze_route
from services.analysis_jobs import AnalysisJobService, AnalysisQueueFullError
from services.comparison_pipeline import ComparisonJobRequest, compare_image_bytes
from services.image_preprocess import ImagePreprocessError, preprocess_image
from services.sensor_evidence import collect_sensor_evidence
from services.validation import ImageValidationError, validate_upload_file

router = APIRouter()


@router.post("/analysis-comparisons", status_code=status.HTTP_202_ACCEPTED)
async def create_comparison(
    request: Request,
    image: UploadFile = File(...),
    capture_id: str | None = Form(default=None),
    capture_time_ms: int | None = Form(default=None),
    camera_facing_mode: str | None = Form(default=None),
    clock_offset_ms: int | None = Form(default=None),
    clock_rtt_ms: int | None = Form(default=None),
) -> JSONResponse:
    try:
        upload = await validate_upload_file(image, analyze_route.settings.max_image_size_mb)
        processed = await anyio.to_thread.run_sync(preprocess_image, upload.data, analyze_route.settings.image_max_dimension)
    except (ImageValidationError, ImagePreprocessError) as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
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
    service: AnalysisJobService = request.app.state.comparison_jobs
    try:
        record = service.enqueue(
            ComparisonJobRequest(
                image_bytes=upload.data,
                filename=upload.filename,
                content_type=upload.content_type,
                width=processed.width,
                height=processed.height,
                capture_id=capture_id,
                sensor_evidence=sensor_evidence,
            )
        )
    except AnalysisQueueFullError as exc:
        return JSONResponse(status_code=503, content={"error": str(exc)}, headers={"Retry-After": "2"})
    return JSONResponse(
        status_code=202,
        content={"job_id": record.job_id, "status": record.status, "poll_url": f"/analysis-comparisons/{record.job_id}"},
    )


@router.get("/analysis-comparisons/{job_id}")
async def get_comparison(request: Request, job_id: str) -> JSONResponse:
    record = request.app.state.comparison_jobs.get(job_id)
    if record is None:
        return JSONResponse(status_code=404, content={"error": "Pekerjaan perbandingan tidak ditemukan."})
    return JSONResponse(
        status_code=200,
        content={"job_id": record.job_id, "status": record.status, "result": record.result, "error": record.error},
    )


async def run_comparison_job(job: ComparisonJobRequest) -> dict[str, object]:
    return await compare_image_bytes(
        job,
        analyze_route.settings,
        analyze_route.gemma_client,
        analyze_route.depth_model,
    )
