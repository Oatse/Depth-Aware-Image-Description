from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from models.depth_anything import DepthAnything
from models.fusion import fuse_description
from models.gemma_client import GemmaClient
from models.sensor_fusion import append_sensor_section, fuse_sensor_reference
from services.evidence_pipeline import AnalysisEvidenceBundle, build_evidence_bundle
from services.sensor_calibration import CalibrationProfile


@dataclass(frozen=True, slots=True)
class ComparisonJobRequest:
    image_bytes: bytes
    filename: str
    content_type: str
    width: int
    height: int
    capture_id: str | None
    sensor_evidence: dict | None


async def compare_image_bytes(
    request: ComparisonJobRequest,
    settings: Settings,
    gemma_client: GemmaClient,
    depth_model: DepthAnything,
) -> dict[str, object]:
    evidence = await build_evidence_bundle(
        request.image_bytes,
        request.filename,
        settings,
        include_gemma=True,
        include_depth=True,
        gemma_client=gemma_client,
        depth_model=depth_model,
    )
    baseline = _render_mode(evidence, "gemma_only")
    depth_aware = _render_mode(evidence, "gemma_depth")
    calibration_validated = False
    if settings.sensor_calibration_path.exists():
        calibration_validated = CalibrationProfile.load(settings.sensor_calibration_path).validated
    contribution = fuse_sensor_reference(request.sensor_evidence, calibration_validated=calibration_validated)
    iot = _render_mode(evidence, "iot_assisted")
    iot["sensor_contribution"] = contribution
    if contribution["status"] == "insufficient":
        iot["success"] = False
        iot["error"] = contribution["reason_code"]
    else:
        iot["final_description"] = append_sensor_section(iot["final_description"], contribution)
        iot["display"]["sensor_contribution"] = contribution
    return {
        "success": True,
        "capture_id": request.capture_id,
        "filename": request.filename,
        "width": request.width,
        "height": request.height,
        "sensor_evidence": request.sensor_evidence,
        "shared_inference": {"gemma_calls": 1, "depth_calls": 1},
        "modes": {
            "gemma_only": baseline,
            "gemma_depth": depth_aware,
            "iot_assisted": iot,
        },
    }


def _render_mode(evidence: AnalysisEvidenceBundle, mode: str) -> dict[str, object]:
    depth_summary = None if mode == "gemma_only" else evidence.depth_summary
    fusion = fuse_description(evidence.gemma_description, depth_summary, mode, evidence.gemma_structured)
    error = evidence.gemma_error or (evidence.depth_error if mode != "gemma_only" else None)
    return {
        "success": error is None,
        "mode": mode,
        "filename": evidence.filename,
        "gemma_description": evidence.gemma_description,
        "gemma_structured": evidence.gemma_structured,
        "depth_summary": depth_summary,
        "final_description": fusion["final_description"],
        "display": fusion["display"],
        "latency": {
            "gemma_ms": evidence.gemma_latency_ms,
            "depth_ms": 0 if mode == "gemma_only" else evidence.depth_latency_ms,
            "fusion_ms": 0,
            "total_ms": evidence.gemma_latency_ms + (0 if mode == "gemma_only" else evidence.depth_latency_ms),
        },
        "depth_map_url": None if mode == "gemma_only" else evidence.depth_map_url,
        "mock": {"gemma": evidence.gemma_mock, "depth": evidence.depth_mock},
        "error": error,
    }
