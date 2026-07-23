import time
from dataclasses import dataclass

from app.config import Settings
from models.gemma_client import DEFAULT_GEMMA_PROMPT, GemmaClient, GemmaClientError
from models.sensor_fusion import append_sensor_section, fuse_sensor_reference
from services.analysis_types import AnalysisMode
from services.image_preprocess import preprocess_image
from services.sensor_calibration import CalibrationProfile


@dataclass(frozen=True)
class PipelineResult:
    success: bool
    filename: str
    mode: AnalysisMode
    gemma_description: str | None
    gemma_structured: dict | None
    final_description: str | None
    latency: dict[str, int]
    mock: dict[str, bool]
    error: str | None
    display: dict | None
    sensor_contribution: dict | None
    analysis_method: str
    gemma_provenance: dict | None


async def analyze_image_bytes(
    image_bytes: bytes,
    filename: str,
    mode: AnalysisMode,
    settings: Settings,
    gemma_client: GemmaClient | None = None,
    sensor_evidence: dict | None = None,
) -> PipelineResult:
    started_at = time.perf_counter()
    processed = preprocess_image(image_bytes, settings.image_max_dimension)
    client = gemma_client or GemmaClient(settings)
    contribution = None
    if mode is AnalysisMode.SENSOR_ASSISTED:
        contribution = fuse_sensor_reference(sensor_evidence, calibration_profile=_calibration_profile(settings), max_pair_disagreement_cm=settings.sensor_pair_disagreement_cm, max_age_ms=settings.sensor_freshness_max_age_ms)
    prompt = _sensor_conditioned_prompt(contribution)
    try:
        gemma_result = await client.describe_image(processed.base64_image, prompt=prompt)
    except GemmaClientError as exc:
        return _failed_result(filename, mode, started_at, str(exc))

    final_description = gemma_result.description
    final_description = append_sensor_section(final_description, contribution, gemma_result.structured)

    provenance = [{"source": "gemma", "text": gemma_result.description}]
    if contribution is not None:
        provenance.append({"source": "sensor", "text": contribution["description"]})
    display = {
        "fusion_strategy": mode.value,
        "visual_description": gemma_result.description,
        "sensor_contribution": contribution,
        "provenance_segments": provenance,
        "system_note": (
            "Gemma menerima konteks jarak frontal sensor yang sudah divalidasi; backend tetap memeriksa provenance dan aturan pengaitan."
            if prompt is not None
            else "Gemma menggunakan prompt visual default tanpa konteks sensor."
        ),
    }
    return PipelineResult(
        success=True,
        filename=filename,
        mode=mode,
        gemma_description=gemma_result.description,
        gemma_structured=gemma_result.structured,
        final_description=final_description,
        latency={
            "gemma_ms": gemma_result.latency_ms,
            "sensor_ms": 0,
            "total_ms": int((time.perf_counter() - started_at) * 1000),
        },
        mock={"gemma": gemma_result.mock},
        error=None,
        display=display,
        sensor_contribution=contribution,
        analysis_method=mode.value,
        gemma_provenance=gemma_result.provenance,
    )


def _sensor_conditioned_prompt(contribution: dict | None) -> str | None:
    if not contribution or contribution.get("status") != "applied":
        return None
    reference = contribution.get("frontal_reference_cm")
    if not isinstance(reference, (int, float)):
        return None
    return (
        "Konteks sensor terverifikasi: dua HC-SR04 yang telah dikalibrasi membaca "
        f"jarak frontal sekitar {reference:.1f} cm. Gunakan angka ini hanya sebagai "
        "referensi frontal; jangan menganggapnya sebagai identitas atau koordinat objek. "
        "Jika menyebut objek paling dekat, pastikan objek tersebut benar-benar tampak pada gambar.\n\n"
        + DEFAULT_GEMMA_PROMPT
    )


def prediction_row(result: PipelineResult) -> dict:
    structured = result.gemma_structured or {}
    contribution = result.sensor_contribution or {}
    return {
        "image_name": result.filename,
        "mode": result.mode.value,
        "analysis_method": result.analysis_method,
        "description_gemma": result.gemma_description or "",
        "main_object": structured.get("main_object", ""),
        "object_position": structured.get("object_position", ""),
        "scene_type": structured.get("scene_type", ""),
        "sensor_status": contribution.get("status", "not_applicable"),
        "sensor_reason_code": contribution.get("reason_code", ""),
        "sensor_1_cm": contribution.get("sensor_1_cm", ""),
        "sensor_2_cm": contribution.get("sensor_2_cm", ""),
        "sensor_1_corrected_cm": contribution.get("sensor_1_corrected_cm", ""),
        "sensor_2_corrected_cm": contribution.get("sensor_2_corrected_cm", ""),
        "sensor_pair_disagreement_cm": contribution.get("pair_disagreement_cm", ""),
        "frontal_reference_cm": contribution.get("frontal_reference_cm", ""),
        "calibration_status": contribution.get("calibration_status", ""),
        "final_description": result.final_description or "",
        "gemma_latency_ms": result.latency.get("gemma_ms", 0),
        "sensor_latency_ms": result.latency.get("sensor_ms", 0),
        "total_latency_ms": result.latency.get("total_ms", 0),
        "error": result.error or "",
    }


def _calibration_profile(settings: Settings) -> CalibrationProfile | None:
    if not settings.sensor_calibration_path.exists():
        return None
    try:
        profile = CalibrationProfile.load(settings.sensor_calibration_path)
        return profile if profile.correction_ready else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _failed_result(
    filename: str,
    mode: AnalysisMode,
    started_at: float,
    error: str,
) -> PipelineResult:
    return PipelineResult(
        success=False,
        filename=filename,
        mode=mode,
        gemma_description=None,
        gemma_structured=None,
        final_description=None,
        latency={"gemma_ms": 0, "sensor_ms": 0, "total_ms": int((time.perf_counter() - started_at) * 1000)},
        mock={"gemma": False},
        error=error,
        display=None,
        sensor_contribution=None,
        analysis_method=mode.value,
        gemma_provenance=None,
    )
