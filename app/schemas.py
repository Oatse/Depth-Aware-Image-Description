from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.analysis_types import AnalysisMode
from services.sensor_types import SensorContributionStatus, SensorEvidenceStatus


class HealthResponse(BaseModel):
    success: bool
    app: str
    backend: str
    gemma: str
    gemma_model: str


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
    samples: dict[str, SensorSampleModel] = Field(default_factory=dict)


class SensorContributionModel(BaseModel):
    status: SensorContributionStatus
    reason_code: str | None = None
    sensor_1_cm: float | None = None
    sensor_2_cm: float | None = None
    sensor_1_corrected_cm: float | None = None
    sensor_2_corrected_cm: float | None = None
    frontal_reference_cm: float | None = None
    pair_disagreement_cm: float | None = None
    calibration_status: str = "not_validated"
    calibration_version: str | None = None
    description: str = ""
    warnings: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    success: bool
    analysis_run_id: str | None = None
    filename: str | None = None
    content_type: str | None = None
    width: int | None = None
    height: int | None = None
    mode: AnalysisMode | None = None
    gemma_description: str | None = None
    gemma_structured: dict[str, Any] | None = None
    final_description: str | None = None
    display: dict[str, Any] | None = None
    latency: dict[str, int] | None = None
    source_image_url: str | None = None
    mock: dict[str, bool] | None = None
    error: str | None = None
    sensor_evidence: SensorEvidenceModel | dict[str, Any] | None = None
    sensor_contribution: SensorContributionModel | None = None
    analysis_method: str | None = None

    @model_validator(mode="after")
    def require_sensor_contribution(self) -> "AnalyzeResponse":
        if self.success and self.mode is AnalysisMode.SENSOR_ASSISTED and self.sensor_contribution is None:
            raise ValueError("sensor_contribution is required for sensor_assisted responses")
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


class StoredCaptureModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: int
    capture_id: str
    batch_id: str
    status: str
    capture_time_ms: int
    camera_facing_mode: str | None = None
    mode: str
    image: dict[str, Any]
    sensor_evidence: SensorEvidenceModel | dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    analysis_attempts: int = 0
    analysis_job_id: str | None = None
    analysis_run_id: str | None = None
    analysis_error: str | None = None
    created_at: str
    updated_at: str


class CaptureCreatedResponse(BaseModel):
    capture: StoredCaptureModel
    capture_count: int


class CaptureListResponse(BaseModel):
    count: int
    captures: list[StoredCaptureModel]


class CaptureCountResponse(BaseModel):
    count: int
    batch_id: str | None = None
