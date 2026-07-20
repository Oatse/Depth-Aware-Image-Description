from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas import AnalyzeResponse
from models.depth_anything import DepthAnything
from models.gemma_client import GemmaClient, GemmaClientError
from services.image_preprocess import ImagePreprocessError, preprocess_image
from services.analysis_types import AnalysisMode, normalize_analysis_mode
from services.pipeline import analyze_image_bytes, prediction_row
from services.result_logger import log_prediction, log_sensor_evidence
from services.sensor_evidence import collect_sensor_evidence
from services.validation import ImageValidationError, validate_upload_file

router = APIRouter()
settings = get_settings()
gemma_client = GemmaClient(settings)
depth_model = DepthAnything(settings)

SUPPORTED_MODES = {mode.value for mode in AnalysisMode} | {"full"}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    request: Request,
    image: UploadFile = File(...),
    mode: str = Form(default="gemma_depth"),
    save_result: bool = Form(default=True),
    capture_id: str | None = Form(default=None),
    capture_time_ms: int | None = Form(default=None),
    camera_facing_mode: str | None = Form(default=None),
    clock_offset_ms: int | None = Form(default=None),
    clock_rtt_ms: int | None = Form(default=None),
) -> JSONResponse:
    try:
        normalized_mode = normalize_analysis_mode(mode)
    except ValueError:
        return _error_response(
            "Mode must be one of gemma_only, depth_only, or gemma_depth.",
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        upload = await validate_upload_file(image, settings.max_image_size_mb)
        processed = preprocess_image(upload.data, settings.image_max_dimension)
    except (ImageValidationError, ImagePreprocessError) as exc:
        return _error_response(str(exc), status.HTTP_400_BAD_REQUEST)

    sensor_evidence = None
    sensor_bridge = getattr(request.app.state, "sensor_bridge", None)
    if capture_time_ms is not None and sensor_bridge is not None:
        sensor_evidence = collect_sensor_evidence(
            sensor_bridge,
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

    pipeline_result = await analyze_image_bytes(
        upload.data,
        upload.filename,
        normalized_mode,
        settings,
        gemma_client,
        depth_model,
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

    response = AnalyzeResponse(
        success=True,
        filename=upload.filename,
        content_type=upload.content_type,
        width=processed.width,
        height=processed.height,
        mode=normalized_mode,
        description_gemma=pipeline_result.gemma_description,
        gemma_description=pipeline_result.gemma_description,
        gemma_structured=pipeline_result.gemma_structured,
        depth_summary=pipeline_result.depth_summary,
        final_description=pipeline_result.final_description,
        display=pipeline_result.display,
        latency=pipeline_result.latency,
        depth_map_url=pipeline_result.depth_map_url,
        mock=pipeline_result.mock,
        error=pipeline_result.error,
        sensor_evidence=sensor_evidence,
        sensor_contribution=pipeline_result.sensor_contribution,
    )

    if save_result and settings.save_results:
        log_prediction(settings.results_dir, prediction_row(pipeline_result))
        if sensor_evidence is not None:
            log_sensor_evidence(
                settings.results_dir,
                image_name=upload.filename,
                mode=normalized_mode,
                evidence=sensor_evidence,
            )

    return JSONResponse(status_code=status.HTTP_200_OK, content=response.model_dump())


def _error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=AnalyzeResponse(success=False, error=message).model_dump(),
    )


def _final_error_response(
    filename: str,
    content_type: str,
    width: int,
    height: int,
    mode: str,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=AnalyzeResponse(
            success=False,
            filename=filename,
            content_type=content_type,
            width=width,
            height=height,
            mode=mode,
            error=message,
        ).model_dump(),
    )

