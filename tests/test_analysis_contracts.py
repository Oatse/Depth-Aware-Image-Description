import pytest
from pydantic import ValidationError

from app.schemas import AnalyzeResponse, SensorContributionModel
from services.analysis_types import AnalysisMode, normalize_analysis_mode
from services.sensor_types import SensorEvidenceStatus, SensorSample, sensor_evidence_from_payload


def test_final_mode_taxonomy_has_exactly_two_modes() -> None:
    assert {mode.value for mode in AnalysisMode} == {"gemma_only", "sensor_assisted"}
    assert normalize_analysis_mode("gemma_only") is AnalysisMode.GEMMA_ONLY
    assert normalize_analysis_mode("sensor_assisted") is AnalysisMode.SENSOR_ASSISTED
    with pytest.raises(ValueError):
        normalize_analysis_mode("unknown")


def test_sensor_sample_allows_signed_age_but_rejects_negative_distance() -> None:
    sample = SensorSample("sensor_1", 10, 100, -1)
    assert sample.age_ms == -1
    with pytest.raises(ValueError, match="distance_cm"):
        SensorSample("sensor_1", -1, 100, 1)


def test_sensor_evidence_requires_capture_id_and_normalizes_legacy_status() -> None:
    with pytest.raises(ValueError, match="capture_id"):
        sensor_evidence_from_payload({"status": "paired", "samples": {}})
    evidence = sensor_evidence_from_payload({
        "capture_id": "cap-1",
        "status": "sensor_pair_conflict",
        "samples": {},
    })
    assert evidence.status is SensorEvidenceStatus.PAIR_CONFLICT


def test_sensor_assisted_response_requires_contribution() -> None:
    with pytest.raises(ValidationError, match="sensor_contribution"):
        AnalyzeResponse(success=True, mode=AnalysisMode.SENSOR_ASSISTED)
    response = AnalyzeResponse(
        success=True,
        mode=AnalysisMode.SENSOR_ASSISTED,
        sensor_contribution=SensorContributionModel(
            status="insufficient",
            reason_code="sensor_unavailable",
        ),
    )
    assert response.mode is AnalysisMode.SENSOR_ASSISTED
