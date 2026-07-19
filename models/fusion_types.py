from enum import StrEnum
from typing import TypedDict


class FusionPolicy(StrEnum):
    EVIDENCE_CONSTRAINED = "evidence_constrained"
    LEGACY_VERBOSE = "legacy_verbose"


class FinalSections(TypedDict):
    visual_description: str
    depth_insight: str
    potential_obstacle: str
    open_area: str
    system_note: str


class ProvenanceSegment(TypedDict):
    source: str
    text: str


class DisplayPayload(TypedDict, total=False):
    visual_summary: str
    depth_status: str
    navigation_region: str
    distance_category: str
    safe_direction: str
    final_sections: FinalSections
    fusion_strategy: str
    provenance_segments: list[ProvenanceSegment]
    system_note: str


class FusionResult(TypedDict):
    final_description: str
    gemma_description: str | None
    depth_summary: dict | None
    warnings: list[str]
    display: DisplayPayload
