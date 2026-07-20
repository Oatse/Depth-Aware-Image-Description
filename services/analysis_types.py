from __future__ import annotations

from enum import StrEnum


class AnalysisMode(StrEnum):
    GEMMA_ONLY = "gemma_only"
    DEPTH_ONLY = "depth_only"
    GEMMA_DEPTH = "gemma_depth"
    IOT_ASSISTED = "iot_assisted"


PUBLIC_ANALYSIS_MODES = frozenset(AnalysisMode)
PRIMARY_COMPARISON_MODES = frozenset(
    {AnalysisMode.GEMMA_ONLY, AnalysisMode.GEMMA_DEPTH, AnalysisMode.IOT_ASSISTED}
)


def normalize_analysis_mode(value: str) -> AnalysisMode:
    if value == "full":
        return AnalysisMode.GEMMA_DEPTH
    try:
        return AnalysisMode(value)
    except ValueError as exc:
        choices = ", ".join(mode.value for mode in AnalysisMode)
        raise ValueError(f"Mode must be one of {choices}.") from exc
