from models.fusion_types import DisplayPayload, FinalSections, FusionPolicy, ProvenanceSegment


def build_display_payload(
    visual_summary: str,
    depth_summary: dict | None,
    mode: str,
    final_description: str,
    final_sections: FinalSections,
    policy: FusionPolicy,
) -> DisplayPayload:
    provenance_segments = [
        segment
        for segment in _provenance_segments(
            mode,
            visual_summary,
            final_description,
            final_sections,
        )
        if segment["text"]
    ]
    if not depth_summary:
        return {
            "visual_summary": visual_summary or "Tidak tersedia",
            "depth_status": "Informasi kedalaman tidak tersedia",
            "navigation_region": "tidak_diketahui",
            "safe_direction": "tidak_diketahui",
            "final_sections": final_sections,
            "fusion_strategy": _fusion_strategy(mode, policy),
            "provenance_segments": provenance_segments,
            "system_note": final_sections["system_note"],
        }
    return {
        "visual_summary": visual_summary or "Tidak tersedia",
        "depth_status": depth_summary.get("warning", "Informasi kedalaman tidak tersedia."),
        "navigation_region": depth_summary.get("nearest_region", "tidak_diketahui"),
        "distance_category": depth_summary.get("distance_category", "tidak_diketahui"),
        "safe_direction": depth_summary.get("safe_direction", "tidak_diketahui"),
        "final_sections": final_sections,
        "fusion_strategy": _fusion_strategy(mode, policy),
        "provenance_segments": provenance_segments,
        "system_note": final_sections["system_note"],
    }


def _fusion_strategy(mode: str, policy: FusionPolicy) -> str:
    if mode == "gemma_depth":
        if policy is FusionPolicy.EVIDENCE_CONSTRAINED:
            return "evidence_constrained_regional_late_fusion"
        return "legacy_verbose_late_fusion"
    if mode == "depth_only":
        return "depth_only_summary"
    return "gemma_visual_spatial_baseline"


def _provenance_segments(
    mode: str,
    visual_summary: str,
    final_description: str,
    final_sections: FinalSections,
) -> list[ProvenanceSegment]:
    if mode == "gemma_depth":
        return [
            {"source": "gemma", "text": visual_summary},
            {"source": "depth", "text": final_sections["depth_insight"]},
            {"source": "inference", "text": final_sections["potential_obstacle"]},
            {"source": "template", "text": final_sections["open_area"]},
        ]
    if mode == "depth_only":
        return [
            {"source": "depth", "text": final_sections["depth_insight"]},
            {"source": "inference", "text": final_sections["potential_obstacle"]},
            {"source": "template", "text": final_sections["open_area"]},
        ]
    return [{"source": "gemma", "text": final_description}]
