import time
from dataclasses import dataclass
from pathlib import Path
from app.config import Settings
from models.depth_anything import DepthAnything
from models.fusion import fuse_description
from services.analysis_types import AnalysisMode
from models.gemma_client import GemmaClient
from services.evidence_pipeline import build_evidence_bundle

GEMMA_MODES = frozenset({AnalysisMode.GEMMA_ONLY, AnalysisMode.GEMMA_DEPTH, AnalysisMode.IOT_ASSISTED})
DEPTH_MODES = frozenset({AnalysisMode.DEPTH_ONLY, AnalysisMode.GEMMA_DEPTH, AnalysisMode.IOT_ASSISTED})


@dataclass(frozen=True)
class PipelineResult:
    success: bool
    filename: str
    mode: str
    gemma_description: str | None
    gemma_structured: dict | None
    depth_summary: dict | None
    final_description: str | None
    latency: dict[str, int]
    depth_map_url: str | None
    mock: dict[str, bool]
    error: str | None
    display: dict | None


async def analyze_image_bytes(
    image_bytes: bytes,
    filename: str,
    mode: str,
    settings: Settings,
    gemma_client: GemmaClient | None = None,
    depth_model: DepthAnything | None = None,
) -> PipelineResult:
    started_at = time.perf_counter()
    evidence = await build_evidence_bundle(
        image_bytes,
        filename,
        settings,
        include_gemma=mode in GEMMA_MODES,
        include_depth=mode in DEPTH_MODES,
        gemma_client=gemma_client,
        depth_model=depth_model,
    )
    if mode == AnalysisMode.DEPTH_ONLY and evidence.depth_error:
        return _failed_result(filename, mode, started_at, evidence.depth_error)
    if mode == AnalysisMode.GEMMA_ONLY and evidence.gemma_error:
        return _failed_result(filename, mode, started_at, evidence.gemma_error)

    fusion_started_at = time.perf_counter()
    fusion = fuse_description(evidence.gemma_description, evidence.depth_summary, mode, evidence.gemma_structured)
    fusion_latency_ms = int((time.perf_counter() - fusion_started_at) * 1000)
    total_latency_ms = int((time.perf_counter() - started_at) * 1000)
    return PipelineResult(
        success=True,
        filename=filename,
        mode=mode,
        gemma_description=evidence.gemma_description,
        gemma_structured=evidence.gemma_structured,
        depth_summary=evidence.depth_summary,
        final_description=fusion["final_description"],
        latency={
            "gemma_ms": evidence.gemma_latency_ms,
            "depth_ms": evidence.depth_latency_ms,
            "fusion_ms": fusion_latency_ms,
            "total_ms": total_latency_ms,
        },
        depth_map_url=evidence.depth_map_url,
        mock={"gemma": evidence.gemma_mock, "depth": evidence.depth_mock},
        error=evidence.gemma_error or evidence.depth_error,
        display=fusion["display"],
    )


def prediction_row(result: PipelineResult) -> dict:
    depth_summary = result.depth_summary or {}
    gemma_structured = result.gemma_structured or {}
    return {
        "image_name": result.filename,
        "mode": result.mode,
        "description_gemma": result.gemma_description or "",
        "main_object": gemma_structured.get("main_object", ""),
        "object_position": gemma_structured.get("object_position", ""),
        "scene_type": gemma_structured.get("scene_type", ""),
        "nearest_region": depth_summary.get("nearest_region", ""),
        "distance_category": depth_summary.get("distance_category", ""),
        "estimated_distance": depth_summary.get("estimated_distance", ""),
        "safe_direction": depth_summary.get("safe_direction", ""),
        "fusion_policy": (result.display or {}).get("fusion_strategy", ""),
        "final_description": result.final_description or "",
        "gemma_latency_ms": result.latency.get("gemma_ms", 0),
        "depth_latency_ms": result.latency.get("depth_ms", 0),
        "total_latency_ms": result.latency.get("total_ms", 0),
        "error": result.error or "",
    }


def _failed_result(filename: str, mode: str, started_at: float, error: str) -> PipelineResult:
    return PipelineResult(
        success=False,
        filename=filename,
        mode=mode,
        gemma_description=None,
        gemma_structured=None,
        depth_summary=None,
        final_description=None,
        latency={"gemma_ms": 0, "depth_ms": 0, "fusion_ms": 0, "total_ms": int((time.perf_counter() - started_at) * 1000)},
        depth_map_url=None,
        mock={"gemma": False, "depth": False},
        error=error,
        display=None,
    )
