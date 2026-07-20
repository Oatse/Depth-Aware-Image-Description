from __future__ import annotations

from dataclasses import dataclass

import anyio

from app.config import Settings
from models.depth_anything import DepthAnything
from models.gemma_client import GemmaClient, GemmaClientError
from services.depth_analysis import analyze_depth_regions
from services.image_preprocess import preprocess_image


@dataclass(frozen=True, slots=True)
class AnalysisEvidenceBundle:
    filename: str
    width: int
    height: int
    gemma_description: str | None
    gemma_structured: dict | None
    gemma_latency_ms: int
    gemma_mock: bool
    gemma_error: str | None
    depth_summary: dict | None
    depth_latency_ms: int
    depth_map_url: str | None
    depth_mock: bool
    depth_error: str | None


async def build_evidence_bundle(
    image_bytes: bytes,
    filename: str,
    settings: Settings,
    *,
    include_gemma: bool,
    include_depth: bool,
    gemma_client: GemmaClient | None = None,
    depth_model: DepthAnything | None = None,
) -> AnalysisEvidenceBundle:
    processed = preprocess_image(image_bytes, settings.image_max_dimension)
    gemma_client = gemma_client or GemmaClient(settings)
    depth_model = depth_model or DepthAnything(settings)
    gemma_description = None
    gemma_structured = None
    gemma_latency_ms = 0
    gemma_mock = False
    gemma_error = None
    if include_gemma:
        try:
            gemma_result = await gemma_client.describe_image(processed.base64_image)
            gemma_description = gemma_result.description
            gemma_structured = gemma_result.structured
            gemma_latency_ms = gemma_result.latency_ms
            gemma_mock = gemma_result.mock
        except GemmaClientError as exc:
            gemma_error = str(exc)

    depth_summary = None
    depth_latency_ms = 0
    depth_map_url = None
    depth_mock = False
    depth_error = None
    if include_depth:
        depth_result = await anyio.to_thread.run_sync(depth_model.estimate, processed.image, filename)
        depth_latency_ms = depth_result.latency_ms
        depth_mock = depth_result.mock
        depth_map_url = _to_depth_map_url(depth_result.depth_map_path)
        if depth_result.success:
            depth_summary = analyze_depth_regions(depth_result.depth_map)
        else:
            depth_error = depth_result.error
    return AnalysisEvidenceBundle(
        filename=filename,
        width=processed.width,
        height=processed.height,
        gemma_description=gemma_description,
        gemma_structured=gemma_structured,
        gemma_latency_ms=gemma_latency_ms,
        gemma_mock=gemma_mock,
        gemma_error=gemma_error,
        depth_summary=depth_summary,
        depth_latency_ms=depth_latency_ms,
        depth_map_url=depth_map_url,
        depth_mock=depth_mock,
        depth_error=depth_error,
    )


def _to_depth_map_url(depth_map_path: str | None) -> str | None:
    if not depth_map_path:
        return None
    normalized = depth_map_path.replace("\\", "/")
    marker = "results/"
    if marker in normalized:
        return "/" + normalized[normalized.index(marker):]
    return normalized
