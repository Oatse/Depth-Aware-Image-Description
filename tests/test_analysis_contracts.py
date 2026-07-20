import pytest
from pydantic import ValidationError

from app.schemas import AnalyzeResponse, SensorContributionModel
from services.analysis_types import AnalysisMode, normalize_analysis_mode
from services.sensor_types import (
    SensorEvidenceStatus,
    SensorSample,
    sensor_evidence_from_payload,
)


def test_final_mode_taxonomy_and_legacy_full_alias() -> None:
    assert normalize_analysis_mode("full") is AnalysisMode.GEMMA_DEPTH
    assert normalize_analysis_mode("iot_assisted") is AnalysisMode.IOT_ASSISTED
    with pytest.raises(ValueError):
        normalize_analysis_mode("unknown")


def test_sensor_sample_rejects_negative_age_and_distance() -> None:
    with pytest.raises(ValueError, match="age_ms"):
        SensorSample("sensor_1", 10, 100, -1)
    with pytest.raises(ValueError, match="distance_cm"):
        SensorSample("sensor_1", -1, 100, 1)


def test_sensor_evidence_requires_capture_id_and_normalizes_legacy_status() -> None:
    with pytest.raises(ValueError, match="capture_id"):
        sensor_evidence_from_payload({"status": "paired", "samples": {}})
    evidence = sensor_evidence_from_payload(
        {
            "capture_id": "cap-1",
            "status": "sensor_pair_conflict",
            "samples": {},
        }
    )
    assert evidence.status is SensorEvidenceStatus.PAIR_CONFLICT


def test_iot_response_requires_sensor_contribution() -> None:
    with pytest.raises(ValidationError, match="sensor_contribution"):
        AnalyzeResponse(success=True, mode=AnalysisMode.IOT_ASSISTED)
    response = AnalyzeResponse(
        success=True,
        mode=AnalysisMode.IOT_ASSISTED,
        sensor_contribution=SensorContributionModel(
            status="insufficient", reason_code="sensor_unavailable"
        ),
    )
    assert response.mode is AnalysisMode.IOT_ASSISTED
