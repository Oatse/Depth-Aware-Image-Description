from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from services.analysis_types import AnalysisMode
from services.sensor_types import SensorContributionStatus, SensorEvidenceStatus


class HealthResponse(BaseModel):
    success: bool
    app: str
    backend: str
    gemma: str
    depth_model: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


class SensorSampleModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    distance_cm: float | None = None
    received_time_ms: int | None = None
    age_ms: int | None = None
    status: str = "ok"


class SensorEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    capture_id: str | None = None
    status: SensorEvidenceStatus | str | None = None
    samples: dict[str, SensorSampleModel] = {}


class SensorContributionModel(BaseModel):
    status: SensorContributionStatus
    reason_code: str | None = None
    frontal_reference_cm: float | None = None
    depth_consistency: str | None = None
    warnings: list[str] = []


class AnalyzeResponse(BaseModel):
    success: bool
    analysis_run_id: str | None = None
    filename: str | None = None
    content_type: str | None = None
    width: int | None = None
    height: int | None = None
    mode: AnalysisMode | None = None
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
    sensor_evidence: SensorEvidenceModel | dict[str, Any] | None = None
    sensor_contribution: SensorContributionModel | None = None

    @model_validator(mode="after")
    def require_iot_contribution(self) -> "AnalyzeResponse":
        if self.success and self.mode is AnalysisMode.IOT_ASSISTED and self.sensor_contribution is None:
            raise ValueError("sensor_contribution is required for iot_assisted responses")
        return self


class AnalysisJobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJobAcceptedResponse(BaseModel):
    job_id: str
    status: AnalysisJobState
    poll_url: str
    queue_scope: str


class AnalysisJobStatusResponse(BaseModel):
    job_id: str
    status: AnalysisJobState
    created_at: str
    updated_at: str
    result: AnalyzeResponse | None = None
    error: str | None = None
