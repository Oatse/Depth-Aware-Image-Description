from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas import AnalyzeResponse
from models.depth_anything import DepthAnything
from models.gemma_client import GemmaClient, GemmaClientError
from services.image_preprocess import ImagePreprocessError, preprocess_image
from services.pipeline import analyze_image_bytes, prediction_row
from services.result_logger import log_prediction
from services.validation import ImageValidationError, validate_upload_file

router = APIRouter()
settings = get_settings()
gemma_client = GemmaClient(settings)
depth_model = DepthAnything(settings)

SUPPORTED_MODES = {"gemma_only", "depth_only", "gemma_depth", "gemma_depth_prompted", "full"}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    image: UploadFile = File(...),
    mode: str = Form(default="gemma_depth"),
    save_result: bool = Form(default=True),
) -> JSONResponse:
    normalized_mode = "gemma_depth" if mode == "full" else mode
    if mode not in SUPPORTED_MODES:
        return _error_response(
            "Mode must be one of gemma_only, depth_only, gemma_depth, or gemma_depth_prompted.",
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        upload = await validate_upload_file(image, settings.max_image_size_mb)
        processed = preprocess_image(upload.data, settings.image_max_dimension)
    except (ImageValidationError, ImagePreprocessError) as exc:
        return _error_response(str(exc), status.HTTP_400_BAD_REQUEST)

    pipeline_result = await analyze_image_bytes(
        upload.data,
        upload.filename,
        normalized_mode,
        settings,
        gemma_client,
        depth_model,
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
    )

    if save_result and settings.save_results:
        log_prediction(settings.results_dir, prediction_row(pipeline_result))

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

