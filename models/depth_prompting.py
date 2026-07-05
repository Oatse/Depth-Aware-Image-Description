from typing import Final


REGION_LABELS: Final[dict[str, str]] = {
    "upper_left": "atas-kiri",
    "upper_center": "atas-tengah",
    "upper_right": "atas-kanan",
    "middle_left": "tengah-kiri",
    "middle_center": "tengah",
    "middle_right": "tengah-kanan",
    "lower_left": "bawah-kiri",
    "lower_center": "bawah-tengah",
    "lower_right": "bawah-kanan",
    "tidak_diketahui": "tidak diketahui",
}

DEPTH_TO_SPATIAL_PROMPT: Final[str] = (
    "Depth-to-Spatial Prompting Schema.\n"
    "Anda adalah sistem image description berbahasa Indonesia untuk eksperimen citra indoor. "
    "Gunakan gambar sebagai sumber semantik utama, lalu gunakan metadata depth berikut sebagai konteks spasial relatif. "
    "Metadata depth berasal dari peta kedalaman monokular 2D, bukan ukuran meter presisi dan bukan instruksi navigasi. "
    "Jangan menyatakan region sebagai identitas objek jika objeknya tidak tampak jelas pada gambar. "
    "Jika metadata menunjukkan area terdekat atau status area depan yang berpotensi menghalangi, sebutkan sebagai potensi halangan visual dengan bahasa hati-hati. "
    "Tulis deskripsi akhir yang natural, maksimal dua kalimat, dengan bahasa hati-hati seperti 'terlihat', 'tampak', "
    "atau 'terbaca secara relatif'. "
    "Balas hanya JSON valid tanpa markdown dengan skema: "
    "{\"scene_type\":\"indoor|non_indoor|tidak_diketahui\","
    "\"main_object\":\"string\","
    "\"object_position\":\"kiri|kanan|tengah|depan|bawah|tidak_diketahui\","
    "\"objects\":[\"string\"],"
    "\"obstacle_candidate\":\"string\","
    "\"description\":\"deskripsi visual-spasial Bahasa Indonesia\"}."
)


def build_depth_spatial_prompt(depth_summary: dict | None) -> str:
    if not depth_summary:
        return DEPTH_TO_SPATIAL_PROMPT + "\nMetadata depth: tidak tersedia."

    nearest_region = str(depth_summary.get("nearest_region") or "tidak_diketahui")
    distance_category = str(depth_summary.get("distance_category") or "tidak_diketahui")
    safe_direction = str(depth_summary.get("safe_direction") or "tidak_diketahui")
    front_area_status = str(depth_summary.get("front_area_status") or "tidak_diketahui")
    nearest_area = REGION_LABELS.get(nearest_region, nearest_region)

    return (
        f"{DEPTH_TO_SPATIAL_PROMPT}\n"
        "Metadata depth relatif:\n"
        f"- nearest_region: {nearest_region} ({nearest_area})\n"
        f"- distance_category: {distance_category}\n"
        f"- front_area_status: {front_area_status}\n"
        f"- relatively_open_area: {safe_direction}\n"
        "Instruksi interpretasi: gunakan metadata ini untuk memperjelas posisi dan kedekatan relatif area, "
        "sebutkan potensi halangan visual jika area terdekat perlu diperhatikan, "
        "tetapi jangan mengubahnya menjadi klaim jarak presisi atau jalur aman."
    )
