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
    "Gunakan gambar sebagai sumber semantik utama untuk menentukan objek, scene, dan posisi objek. "
    "Gunakan metadata depth hanya sebagai konteks spasial relatif setelah objek visual dari gambar teridentifikasi. "
    "Metadata depth berasal dari peta kedalaman monokular 2D, bukan ukuran meter presisi dan bukan instruksi navigasi. "
    "Metadata depth tidak berisi identitas objek dan tidak boleh mengganti objek utama yang terlihat pada gambar. "
    "Jangan menyatakan region sebagai identitas objek jika objeknya tidak tampak jelas pada gambar. "
    "Pertahankan objek spesifik seperti meja, kursi, pintu, kulkas, atau lampu jika terlihat, dan jangan menggeneralisasikannya menjadi 'perabotan' kecuali objeknya memang tidak jelas. "
    "Jika kategori depth sangat_dekat atau dekat, sebutkan potensi halangan visual dengan bahasa hati-hati. "
    "Jika kategori depth sedang, tulis sebagai jarak relatif sedang dan jangan otomatis menyebutnya halangan dekat. "
    "Jika metadata open-area berada pada region yang juga memuat objek visual, tulis sebagai indikasi relatif dari depth, bukan area kosong atau area bebas objek. "
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
        f"- relatively_open_region: {safe_direction}\n"
        "Instruksi interpretasi: identifikasi objek dari gambar terlebih dahulu, lalu gunakan metadata ini untuk memperjelas posisi dan kedekatan relatif region. "
        "Sebutkan potensi halangan visual hanya untuk kategori sangat_dekat atau dekat, "
        "perlakukan kategori sedang sebagai jarak relatif sedang, "
        "dan jangan menyebut region relatif lapang sebagai area kosong, area aman, atau bebas objek. "
        "Jangan mengubah metadata depth menjadi klaim jarak presisi atau jalur aman."
    )
