from __future__ import annotations

from enum import StrEnum


class AnalysisMode(StrEnum):
    GEMMA_ONLY = "gemma_only"
    SENSOR_ASSISTED = "sensor_assisted"


PUBLIC_ANALYSIS_MODES = frozenset(AnalysisMode)


def normalize_analysis_mode(value: str) -> AnalysisMode:
    try:
        return AnalysisMode(value)
    except ValueError as exc:
        choices = ", ".join(mode.value for mode in AnalysisMode)
        raise ValueError(f"Mode must be one of {choices}.") from exc
