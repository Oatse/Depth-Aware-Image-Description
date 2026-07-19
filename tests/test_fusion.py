from models.fusion import fuse_description
from models.fusion_types import FusionPolicy


def test_fusion_returns_gemma_only_when_depth_missing() -> None:
    result = fuse_description("Terlihat kursi di depan ruangan.", None, "gemma_depth")

    assert result["final_description"] == "Terlihat kursi di depan ruangan."
    assert result["warnings"] == []


def test_gemma_baseline_display_explains_depth_metadata_is_not_extracted() -> None:
    result = fuse_description("Terlihat kursi di depan ruangan.", None, "gemma_only")

    assert result["final_description"] == "Terlihat kursi di depan ruangan."
    assert result["display"]["fusion_strategy"] == "gemma_visual_spatial_baseline"
    assert "Tidak diekstrak sebagai metadata depth" in result["display"]["final_sections"]["depth_insight"]
    assert "bukan indikator depth terstruktur" in result["display"]["final_sections"]["potential_obstacle"]


def test_fusion_adds_warning_for_close_depth() -> None:
    summary = {
        "warning": "Area bawah-tengah menunjukkan potensi halangan visual dekat.",
        "distance_category": "dekat",
        "nearest_region": "lower_center",
        "safe_direction": "kanan",
    }

    result = fuse_description("Terlihat meja di tengah ruangan.", summary, "gemma_depth")

    assert "Berdasarkan grid depth 3x3" in result["final_description"]
    assert "region bawah-tengah" in result["final_description"]
    assert "kategori kedalaman relatif dekat" in result["final_description"]
    assert "Region kanan terbaca relatif lebih lapang" not in result["final_description"]
    assert "bukan pengukuran jarak presisi" not in result["final_description"]
    assert "bukan pengukuran jarak presisi" in result["display"]["system_note"]
    assert "jalan aman" not in result["final_description"].lower()
    assert result["warnings"]


def test_fusion_keeps_depth_claims_regional_when_object_identity_is_unknown() -> None:
    summary = {
        "warning": "Area bawah-kanan memiliki objek pada jarak sedang.",
        "distance_category": "sedang",
        "nearest_region": "lower_right",
        "safe_direction": "tengah",
    }

    result = fuse_description("Sebuah ruangan interior dengan tanaman pot di area depan.", summary, "gemma_depth")

    assert "region bawah-kanan" in result["final_description"]
    assert "kategori kedalaman relatif sedang" in result["final_description"]
    assert "tanaman" not in result["display"]["final_sections"]["depth_insight"]
    assert "Region tengah terbaca relatif lebih lapang" not in result["final_description"]
    assert result["display"]["final_sections"]["depth_insight"].startswith("Berdasarkan estimasi kedalaman")


def test_fusion_keeps_limitation_note_when_visual_summary_has_two_sentences() -> None:
    summary = {
        "warning": "Area bawah-tengah menunjukkan potensi halangan visual sangat dekat.",
        "distance_category": "sangat_dekat",
        "nearest_region": "lower_center",
        "safe_direction": "kiri",
    }

    result = fuse_description(
        "Terlihat area dalam ruangan dengan beberapa objek. Deskripsi visual masih bersifat umum.",
        summary,
        "gemma_depth",
    )

    assert "bukan pengukuran jarak presisi" not in result["final_description"]
    assert "rekomendasi navigasi aman" not in result["final_description"]
    assert "bukan pengukuran jarak presisi" in result["display"]["system_note"]
    assert "rekomendasi navigasi aman" in result["display"]["system_note"]


def test_depth_only_description_does_not_require_gemma() -> None:
    summary = {
        "warning": "Area depan tampak relatif lapang berdasarkan estimasi kedalaman.",
        "distance_category": "jauh",
        "safe_direction": "tengah",
    }

    result = fuse_description(None, summary, "depth_only")

    assert result["final_description"].startswith("Berdasarkan estimasi kedalaman")


def test_evidence_constrained_fusion_keeps_depth_claim_regional_and_concise() -> None:
    # Given
    summary = {
        "warning": "Area bawah-kanan menunjukkan potensi halangan visual dekat.",
        "distance_category": "dekat",
        "nearest_region": "lower_right",
        "safe_direction": "kiri",
    }

    # When
    result = fuse_description(
        "Terlihat sebuah kursi di sisi kiri ruangan.",
        summary,
        "gemma_depth",
        {"main_object": "kursi", "object_position": "kiri"},
        policy=FusionPolicy.EVIDENCE_CONSTRAINED,
    )

    # Then
    description = result["final_description"]
    assert "region bawah-kanan" in description
    assert "kategori kedalaman relatif dekat" in description
    assert "kursi" not in result["display"]["final_sections"]["depth_insight"]
    assert "Region kiri terbaca relatif lebih lapang" not in description
    assert description.count(".") <= 3
    assert result["display"]["fusion_strategy"] == "evidence_constrained_regional_late_fusion"


def test_legacy_policy_remains_available_only_for_controlled_comparison() -> None:
    # Given
    summary = {
        "warning": "Area bawah-kanan menunjukkan potensi halangan visual dekat.",
        "distance_category": "dekat",
        "nearest_region": "lower_right",
        "safe_direction": "kiri",
    }

    # When
    result = fuse_description(
        "Terlihat sebuah kursi di sisi kiri ruangan.",
        summary,
        "gemma_depth",
        policy=FusionPolicy.LEGACY_VERBOSE,
    )

    # Then
    assert "Region kiri terbaca relatif lebih lapang" in result["final_description"]
