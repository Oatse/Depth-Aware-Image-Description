import time
from dataclasses import dataclass
from pathlib import Path

import anyio

from app.config import Settings
from models.depth_anything import DepthAnything
from models.fusion import fuse_description
from models.gemma_client import GemmaClient, GemmaClientError
from services.depth_analysis import analyze_depth_regions
from services.image_preprocess import preprocess_image

GEMMA_MODES = frozenset({"gemma_only", "gemma_depth"})
DEPTH_MODES = frozenset({"depth_only", "gemma_depth"})


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
    processed = preprocess_image(image_bytes, settings.image_max_dimension)
    gemma_client = gemma_client or GemmaClient(settings)
    depth_model = depth_model or DepthAnything(settings)

    gemma_description: str | None = None
    gemma_structured: dict | None = None
    gemma_latency_ms = 0
    gemma_mock = False
    gemma_error: str | None = None

    depth_summary: dict | None = None
    depth_latency_ms = 0
    depth_map_url: str | None = None
    depth_mock = False
    depth_error: str | None = None
    if mode in DEPTH_MODES:
        depth_result = await anyio.to_thread.run_sync(depth_model.estimate, processed.image, filename)
        depth_latency_ms = depth_result.latency_ms
        depth_mock = depth_result.mock
        depth_map_url = _to_depth_map_url(depth_result.depth_map_path)
        if depth_result.success:
            depth_summary = analyze_depth_regions(
                depth_result.depth_map,
            )
        else:
            depth_error = depth_result.error
            if mode == "depth_only":
                return _failed_result(filename, mode, started_at, depth_error or "Depth inference failed.")

    if mode in GEMMA_MODES:
        try:
            gemma_result = await gemma_client.describe_image(processed.base64_image)
            gemma_description = gemma_result.description
            gemma_structured = gemma_result.structured
            gemma_latency_ms = gemma_result.latency_ms
            gemma_mock = gemma_result.mock
        except GemmaClientError as exc:
            gemma_error = str(exc)
            if mode == "gemma_only":
                return _failed_result(filename, mode, started_at, gemma_error)

    fusion_started_at = time.perf_counter()
    fusion = fuse_description(gemma_description, depth_summary, mode, gemma_structured)
    fusion_latency_ms = int((time.perf_counter() - fusion_started_at) * 1000)
    total_latency_ms = int((time.perf_counter() - started_at) * 1000)
    return PipelineResult(
        success=True,
        filename=filename,
        mode=mode,
        gemma_description=gemma_description,
        gemma_structured=gemma_structured,
        depth_summary=depth_summary,
        final_description=fusion["final_description"],
        latency={
            "gemma_ms": gemma_latency_ms,
            "depth_ms": depth_latency_ms,
            "fusion_ms": fusion_latency_ms,
            "total_ms": total_latency_ms,
        },
        depth_map_url=depth_map_url,
        mock={"gemma": gemma_mock, "depth": depth_mock},
        error=gemma_error or depth_error,
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


def _to_depth_map_url(depth_map_path: str | None) -> str | None:
    if not depth_map_path:
        return None
    normalized = depth_map_path.replace("\\", "/")
    marker = "results/"
    if marker in normalized:
        return "/" + normalized[normalized.index(marker):]
    return normalized
