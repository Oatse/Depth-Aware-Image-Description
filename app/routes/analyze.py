from uuid import uuid4

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas import AnalyzeResponse
from models.gemma_client import GemmaClient
from services.analysis_types import AnalysisMode, normalize_analysis_mode
from services.image_preprocess import ImagePreprocessError, preprocess_image
from services.pipeline import analyze_image_bytes, prediction_row
from services.result_logger import log_analysis_run, log_prediction, log_sensor_evidence, save_source_image
from services.sensor_evidence import collect_sensor_evidence
from services.validation import ImageValidationError, validate_upload_file

router = APIRouter()
settings = get_settings()
gemma_client = GemmaClient(settings)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
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
        return _error_response(str(exc), status.HTTP_400_BAD_REQUEST)
    try:
        upload = await validate_upload_file(image, settings.max_image_size_mb)
        processed = preprocess_image(upload.data, settings.image_max_dimension)
    except (ImageValidationError, ImagePreprocessError) as exc:
        return _error_response(str(exc), status.HTTP_400_BAD_REQUEST)

    sensor_evidence = _collect_sensor_evidence(
        request,
        capture_id=capture_id,
        capture_time_ms=capture_time_ms,
        camera_facing_mode=camera_facing_mode,
        clock_offset_ms=clock_offset_ms,
        clock_rtt_ms=clock_rtt_ms,
    )
    pipeline_result = await analyze_image_bytes(
        upload.data,
        upload.filename,
        normalized_mode,
        settings,
        gemma_client,
        sensor_evidence,
    )
    if not pipeline_result.success:
        return _final_error_response(
            upload.filename,
            upload.content_type,
            processed.width,
            processed.height,
            normalized_mode,
            pipeline_result.error or "Analyze failed.",
        )

    analysis_run_id = uuid4().hex
    source_image = None
    if save_result and settings.save_results:
        source_image = save_source_image(settings.results_dir, upload.data, upload.filename, analysis_run_id)
    response = AnalyzeResponse(
        success=True,
        analysis_run_id=analysis_run_id,
        filename=upload.filename,
        content_type=upload.content_type,
        width=processed.width,
        height=processed.height,
        mode=normalized_mode,
        gemma_description=pipeline_result.gemma_description,
        gemma_structured=pipeline_result.gemma_structured,
        final_description=pipeline_result.final_description,
        display=pipeline_result.display,
        latency=pipeline_result.latency,
        source_image_url=(source_image or {}).get("url"),
        mock=pipeline_result.mock,
        sensor_evidence=sensor_evidence,
        sensor_contribution=pipeline_result.sensor_contribution,
        analysis_method=pipeline_result.analysis_method,
    )
    if save_result and settings.save_results:
        log_analysis_run(
            settings.results_dir,
            analysis_run_id=analysis_run_id,
            capture_id=capture_id,
            filename=upload.filename,
            sensor_evidence=sensor_evidence,
            outputs={normalized_mode.value: response.model_dump(mode="json")},
            source_image=source_image,
        )
        log_prediction(settings.results_dir, prediction_row(pipeline_result))
        if sensor_evidence is not None:
            log_sensor_evidence(
                settings.results_dir,
                image_name=upload.filename,
                mode=normalized_mode,
                evidence=sensor_evidence,
            )
    return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump(mode="json"))


def _collect_sensor_evidence(
    request: Request,
    *,
    capture_id: str | None,
    capture_time_ms: int | None,
    camera_facing_mode: str | None,
    clock_offset_ms: int | None,
    clock_rtt_ms: int | None,
) -> dict | None:
    bridge = getattr(request.app.state, "sensor_bridge", None)
    if capture_time_ms is None or bridge is None:
        return None
    return collect_sensor_evidence(
        bridge,
        capture_id=capture_id,
        client_capture_time_ms=capture_time_ms,
        camera_facing_mode=camera_facing_mode,
        match_window_ms=settings.sensor_match_window_ms,
        max_clock_skew_ms=settings.sensor_max_clock_skew_ms,
        clock_offset_ms=clock_offset_ms,
        clock_rtt_ms=clock_rtt_ms,
        max_clock_rtt_ms=settings.sensor_clock_rtt_max_ms,
        freshness_max_age_ms=settings.sensor_freshness_max_age_ms,
        pair_disagreement_cm=settings.sensor_pair_disagreement_cm,
    )


def _error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=AnalyzeResponse(success=False, error=message).model_dump(mode="json"),
    )


def _final_error_response(
    filename: str,
    content_type: str,
    width: int,
    height: int,
    mode: AnalysisMode,
    message: str,
) -> JSONResponse:
    response = AnalyzeResponse(
        success=False,
        filename=filename,
        content_type=content_type,
        width=width,
        height=height,
        mode=mode,
        error=message,
    )
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content=response.model_dump(mode="json"))
