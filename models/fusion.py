from models.fusion_display import build_display_payload
from models.fusion_terms import DEPTH_LIMITATION_NOTE, DISTANCE_LABELS, REGION_LABELS
from models.fusion_types import DisplayPayload, FinalSections, FusionPolicy, FusionResult


def fuse_description(
    gemma_description: str | None,
    depth_summary: dict | None,
    mode: str = "gemma_depth",
    gemma_structured: dict | None = None,
    *,
    policy: FusionPolicy = FusionPolicy.EVIDENCE_CONSTRAINED,
) -> FusionResult:
    warnings: list[str] = []
    cleaned_gemma = _clean_text(gemma_description)
    visual_summary = _visual_summary(cleaned_gemma, gemma_structured)
    if mode == "depth_only":
        final_description = _depth_only_description(depth_summary)
        warnings.extend(_warnings_from_depth(depth_summary))
        return {
            "final_description": final_description,
            "gemma_description": visual_summary or cleaned_gemma or None,
            "depth_summary": depth_summary,
            "warnings": warnings,
            "display": _display_payload(visual_summary, depth_summary, mode, final_description, policy),
        }

    if not depth_summary:
        final_description = visual_summary or cleaned_gemma or "Deskripsi visual tidak tersedia."
        return {
            "final_description": final_description,
            "gemma_description": visual_summary or cleaned_gemma or None,
            "depth_summary": None,
            "warnings": warnings,
            "display": _display_payload(visual_summary or cleaned_gemma, None, mode, final_description, policy),
        }

    warnings.extend(_warnings_from_depth(depth_summary))
    if policy is FusionPolicy.EVIDENCE_CONSTRAINED:
        final_description = _evidence_constrained_description(visual_summary, depth_summary)
        final_description = _limit_sentences(_clean_text(final_description), 3, 700)
    else:
        final_description = _depth_aware_description(visual_summary, depth_summary)
        final_description = _limit_sentences(_clean_text(final_description), 6, 1100)

    return {
        "final_description": final_description,
        "gemma_description": visual_summary or cleaned_gemma or None,
        "depth_summary": depth_summary,
        "warnings": warnings,
        "display": _display_payload(
            visual_summary or cleaned_gemma,
            depth_summary,
            mode,
            final_description,
            policy,
        ),
    }


def _as_sentence_fragment(text: str) -> str:
    cleaned = _clean_text(text).rstrip(".")
    if not cleaned:
        return cleaned
    return cleaned[0].lower() + cleaned[1:]


def _clean_text(text: str | None) -> str:
    if not text:
        return ""
    replacements = {
        "**": "",
        "__": "",
        "`": "",
        "#": "",
    }
    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return " ".join(cleaned.split()).strip()


def _visual_summary(gemma_description: str, structured: dict | None) -> str:
    if not structured:
        return _limit_sentences(gemma_description, 2, 360)
    description = _clean_text(structured.get("description"))
    main_object = structured.get("main_object")
    position = structured.get("object_position")
    if description and description != "tidak_diketahui":
        return _limit_sentences(description, 2, 360)
    if main_object and main_object != "tidak_diketahui":
        return f"Terlihat {main_object} di area {position or 'tidak_diketahui'}."
    return _limit_sentences(gemma_description, 2, 360)


def _depth_only_description(depth_summary: dict | None) -> str:
    if not depth_summary:
        return "Informasi kedalaman tidak tersedia."
    return _clean_text(_depth_aware_description("", depth_summary))


def _depth_aware_description(visual_summary: str, depth_summary: dict) -> str:
    sections = _final_sections(visual_summary, depth_summary)
    parts = [
        sections["visual_description"],
        sections["depth_insight"],
        sections["potential_obstacle"],
        sections["open_area"],
    ]
    return " ".join(part for part in parts if part)


def _evidence_constrained_description(visual_summary: str, depth_summary: dict) -> str:
    nearest_region = _region_label(depth_summary.get("nearest_region"))
    distance_category = _distance_label(depth_summary.get("distance_category"))
    depth_sentence = _evidence_constrained_depth_sentence(nearest_region, distance_category)
    return " ".join(part for part in (visual_summary, depth_sentence) if part)


def _evidence_constrained_depth_sentence(nearest_region: str, distance_category: str) -> str:
    if nearest_region == "tidak diketahui" or distance_category == "tidak diketahui":
        return "Estimasi depth belum cukup untuk menyatakan region terdekat dan kategori kedalaman relatif."
    base = (
        f"Berdasarkan grid depth 3x3, region {nearest_region} memiliki "
        f"kategori kedalaman relatif {distance_category} dibanding region lain dalam citra"
    )
    if distance_category in {"sangat dekat", "dekat"}:
        return f"{base} dan menunjukkan potensi halangan visual pada region tersebut."
    return f"{base}."


def _final_sections(visual_summary: str, depth_summary: dict | None, mode: str = "gemma_depth") -> FinalSections:
    if not depth_summary:
        if mode == "gemma_only":
            return {
                "visual_description": visual_summary,
                "depth_insight": "Tidak diekstrak sebagai metadata depth pada mode Gemma Baseline.",
                "potential_obstacle": "Gemma dapat menyebut potensi hambatan bila terlihat, tetapi bukan indikator depth terstruktur.",
                "open_area": "Area relatif lapang tidak dihitung sebagai metadata depth pada mode ini.",
                "system_note": DEPTH_LIMITATION_NOTE,
            }
        return {
            "visual_description": visual_summary,
            "depth_insight": "Informasi kedalaman tidak tersedia.",
            "potential_obstacle": "Potensi halangan visual belum dapat ditentukan.",
            "open_area": "Area relatif lapang belum dapat ditentukan.",
            "system_note": DEPTH_LIMITATION_NOTE,
        }

    nearest_region = _region_label(depth_summary.get("nearest_region"))
    distance_category = _distance_label(depth_summary.get("distance_category"))
    return {
        "visual_description": visual_summary,
        "depth_insight": _depth_sentence(nearest_region, distance_category),
        "potential_obstacle": _obstacle_sentence(nearest_region, distance_category),
        "open_area": _direction_text(depth_summary.get("safe_direction")),
        "system_note": DEPTH_LIMITATION_NOTE,
    }


def _depth_sentence(nearest_region: str, distance_category: str) -> str:
    if nearest_region == "tidak diketahui" or distance_category == "tidak diketahui":
        return "Berdasarkan estimasi kedalaman relatif, region terdekat atau kategori kedalaman relatif belum cukup terbaca."
    return (
        "Berdasarkan estimasi kedalaman relatif, "
        f"bagian {nearest_region} merupakan area yang paling dekat dibanding area lain, "
        f"dengan kategori kedalaman relatif {distance_category}."
    )


def _obstacle_sentence(nearest_region: str, distance_category: str) -> str:
    if nearest_region == "tidak diketahui" or distance_category == "tidak diketahui":
        return "Potensi halangan visual belum dapat ditentukan dari peta kedalaman."
    if distance_category == "sedang":
        return (
            f"Area {nearest_region} terbaca pada jarak relatif sedang, "
            "sehingga tidak otomatis diperlakukan sebagai halangan visual dekat."
        )
    if distance_category == "jauh":
        return (
            f"Area {nearest_region} tidak menunjukkan potensi halangan visual yang kuat "
            "karena masih berada pada kategori kedalaman relatif jauh."
        )
    return (
        f"Area {nearest_region} berpotensi menjadi halangan visual "
        "karena posisinya terbaca lebih dekat dibanding area lain."
    )


def _direction_text(direction: str | None) -> str:
    if direction in {"kiri", "kanan"}:
        return (
            f"Region {direction} terbaca relatif lebih lapang menurut estimasi depth, "
            "bukan berarti bebas objek."
        )
    if direction == "tengah":
        return (
            "Region tengah terbaca relatif lebih lapang menurut estimasi depth, "
            "bukan berarti bebas objek."
        )
    return "Arah yang lebih lapang belum dapat ditentukan."


def _region_label(value: str | None) -> str:
    return REGION_LABELS.get(value or "tidak_diketahui", value or "tidak diketahui")


def _distance_label(value: str | None) -> str:
    return DISTANCE_LABELS.get(value or "tidak_diketahui", (value or "tidak diketahui").replace("_", " "))


def _warnings_from_depth(depth_summary: dict | None) -> list[str]:
    if not depth_summary:
        return []
    category = depth_summary.get("distance_category")
    warning = depth_summary.get("warning")
    if category in {"sangat_dekat", "dekat"} and warning:
        return [warning]
    return []


def _limit_sentences(text: str, max_sentences: int, max_chars: int) -> str:
    if not text:
        return ""
    parts = [part.strip() for part in text.replace("?", ".").replace("!", ".").split(".") if part.strip()]
    if not parts:
        return text[:max_chars].strip()
    limited = ". ".join(parts[:max_sentences]).strip()
    if limited and not limited.endswith("."):
        limited += "."
    return limited[:max_chars].strip()


def _display_payload(
    visual_summary: str,
    depth_summary: dict | None,
    mode: str,
    final_description: str,
    policy: FusionPolicy,
) -> DisplayPayload:
    final_sections = _final_sections(visual_summary, depth_summary, mode)
    return build_display_payload(
        visual_summary,
        depth_summary,
        mode,
        final_description,
        final_sections,
        policy,
    )
