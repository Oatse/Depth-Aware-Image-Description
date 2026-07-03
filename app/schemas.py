from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    success: bool
    app: str
    backend: str
    gemma: str
    depth_model: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


class AnalyzeResponse(BaseModel):
    success: bool
    filename: str | None = None
    content_type: str | None = None
    width: int | None = None
    height: int | None = None
    mode: str | None = None
    description_gemma: str | None = None
    gemma_description: str | None = None
    gemma_structured: dict[str, Any] | None = None
    depth_summary: dict[str, Any] | None = None
    final_description: str | None = None
    display: dict[str, Any] | None = None
    latency: dict[str, int] | None = None
    depth_map_url: str | None = None
    mock: dict[str, bool] | None = None
    error: str | None = None
