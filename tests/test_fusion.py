from models.fusion import fuse_description


def test_fusion_returns_gemma_only_when_depth_missing() -> None:
    result = fuse_description("Terlihat kursi di depan ruangan.", None, "gemma_depth")

    assert result["final_description"] == "Terlihat kursi di depan ruangan."
    assert result["warnings"] == []


def test_fusion_adds_warning_for_close_depth() -> None:
    summary = {
        "warning": "Terdapat hambatan dekat di area lower_center.",
        "distance_category": "dekat",
        "nearest_region": "lower_center",
        "safe_direction": "kanan",
    }

    result = fuse_description("Terlihat meja di tengah ruangan.", summary, "gemma_depth")

    assert "Berdasarkan estimasi kedalaman" in result["final_description"]
    assert "bagian bawah-tengah merupakan area yang paling dekat dibanding area lain" in result["final_description"]
    assert "kategori jarak dekat" in result["final_description"]
    assert "Area kanan tampak relatif lebih lapang" in result["final_description"]
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

    assert "bagian bawah-kanan merupakan area yang paling dekat dibanding area lain" in result["final_description"]
    assert "meskipun masih berada pada kategori jarak sedang" in result["final_description"]
    assert "Area bawah-kanan berpotensi menjadi halangan visual" in result["final_description"]
    assert "Area tengah tampak relatif lebih lapang" in result["final_description"]
    assert result["display"]["final_sections"]["depth_insight"].startswith("Berdasarkan estimasi kedalaman")


def test_fusion_keeps_limitation_note_when_visual_summary_has_two_sentences() -> None:
    summary = {
        "warning": "Terdapat hambatan sangat dekat di area bawah-tengah.",
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
