import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SCORES = {
    "VE-001": (4, 4, 4, 4, 3, 0, "Isi tampak konsisten, tetapi identitas koper tidak disebut pada close-up."),
    "VE-002": (5, 4, 4, 4, 4, 0, "Koper, roda, warna, dan tekstur sesuai citra."),
    "VE-003": (5, 4, 5, 5, 4, 0, "Objek dan konteks ruangan sesuai; posisi hanya dinyatakan umum."),
    "VE-004": (5, 4, 5, 5, 4, 0, "Koper, lantai, dan dinding sesuai citra."),
    "VE-005": (5, 4, 5, 4, 4, 0, "Deskripsi sesuai; kata bersih bersifat interpretatif ringan."),
    "VE-006": (5, 5, 4, 4, 4, 0, "Koper close-up, roda, tekstur, dan posisi sesuai."),
    "VE-007": (3, 3, 4, 4, 3, 0, "Objek terlalu generik dan disebut bagian bawah meski bagian depan dominan terlihat."),
    "VE-008": (5, 4, 5, 5, 4, 0, "Objek dan konteks ruangan sesuai citra."),
    "VE-009": (5, 4, 5, 5, 4, 0, "Koper dan kabel di kanan sesuai citra."),
    "VE-010": (5, 5, 5, 5, 4, 0, "Identitas, posisi, lantai, dan dinding sesuai."),
    "VE-011": (5, 4, 5, 5, 4, 0, "Deskripsi akhir tepat meski label awal memberi alternatif kotak penyimpanan."),
    "VE-012": (5, 5, 5, 5, 4, 0, "Koper dominan di bagian depan sesuai citra."),
    "VE-013": (5, 4, 5, 5, 4, 0, "Objek dan latar sesuai; posisi hanya umum."),
    "VE-014": (5, 5, 5, 5, 4, 0, "Objek dominan di tengah dan konteks sesuai."),
    "VE-015": (5, 5, 5, 5, 4, 0, "Koper, lantai, dinding, dan posisi sesuai."),
    "VE-016": (4, 4, 4, 4, 3, 0, "Permukaan close-up dijelaskan tepat, tetapi identitas koper tidak disebut."),
    "VE-017": (4, 5, 4, 4, 3, 0, "Bentuk dan roda sesuai, tetapi identitas dibuat ambigu sebagai wadah."),
    "VE-018": (5, 5, 5, 5, 4, 0, "Koper dan dua batang pegangan sesuai citra."),
    "VE-019": (5, 4, 5, 5, 4, 0, "Objek, lantai, dan dinding sesuai citra."),
    "VE-020": (5, 4, 4, 4, 3, 0, "Objek sesuai; kalimat ketiadaan hambatan menambah sedikit informasi visual."),
    "VE-021": (5, 5, 5, 5, 4, 0, "Koper dominan dan posisi sesuai citra."),
    "VE-022": (5, 5, 5, 5, 4, 0, "Objek dan posisi tepat dengan konteks yang sesuai."),
    "VE-023": (4, 3, 4, 4, 3, 0, "Objek utama cukup tepat, tetapi closest_object tidak ditentukan dan uraian sangat umum."),
    "VE-024": (4, 4, 4, 4, 3, 0, "Permukaan dan benda terang sesuai, tetapi identitas objek utama tidak disebut."),
    "VE-025": (5, 5, 5, 5, 4, 0, "Objek, posisi, dan lingkungan sesuai citra."),
    "VE-026": (5, 5, 5, 5, 4, 0, "Koper dominan di depan sesuai citra."),
    "VE-027": (5, 5, 5, 5, 4, 0, "Objek dan posisi sesuai; alternatif tas masih wajar."),
    "VE-028": (5, 5, 5, 5, 4, 0, "Koper beroda, lantai, dan dinding sesuai."),
    "VE-029": (5, 5, 5, 5, 4, 0, "Objek, posisi, lantai, dan dinding sesuai."),
    "VE-030": (4, 4, 4, 4, 3, 0, "Permukaan close-up tepat, tetapi identitas koper tidak disebut."),
    "VE-031": (5, 5, 5, 5, 4, 0, "Koper, roda, dan posisi sesuai citra."),
    "VE-032": (5, 4, 5, 5, 4, 0, "Objek dan lingkungan sesuai; posisi tidak dirinci."),
    "VE-033": (4, 4, 4, 4, 3, 0, "Permukaan dan benda terang sesuai, tetapi identitas koper tidak disebut."),
    "VE-034": (4, 4, 4, 4, 3, 0, "Isi close-up konsisten, namun deskripsi sangat generik."),
    "VE-035": (5, 5, 5, 5, 4, 0, "Koper, roda, posisi, lantai, dan dinding sesuai."),
    "VE-036": (5, 4, 5, 5, 4, 0, "Objek dan lingkungan sesuai; posisi hanya tersirat."),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_scores(input_path: Path, lock_path: Path) -> dict[str, object]:
    source_sha256 = _sha256(input_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    item_ids = {str(row["evaluation_item_id"]) for row in rows}
    if item_ids != set(SCORES):
        raise ValueError("Daftar item blind tidak sama dengan skor yang dikunci.")
    for row in rows:
        item_id = str(row["evaluation_item_id"])
        object_score, spatial, clarity, naturalness, completeness, unsupported, notes = SCORES[item_id]
        row.update(
            {
                "manual_review_status": "completed",
                "object_consistency": object_score,
                "spatial_consistency": spatial,
                "clarity": clarity,
                "naturalness": naturalness,
                "scene_completeness": completeness,
                "unsupported_claims": unsupported,
                "evaluator_notes": notes,
            }
        )
    with input_path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    lock = {
        "schema_version": 1,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "evaluator_role": "auditor evaluasi dataset multimodal independen",
        "evaluation_design": "single_evaluator_blind_to_mode_distance_capture_and_run",
        "item_count": len(rows),
        "unique_score_item_ids": len(item_ids),
        "source_template_sha256": source_sha256,
        "scored_template_sha256": _sha256(input_path),
        "rubric_scale": {
            "object_consistency": "1-5",
            "spatial_consistency": "1-5",
            "clarity": "1-5",
            "naturalness": "1-5",
            "scene_completeness": "1-5",
            "unsupported_claims": "count",
        },
        "key_opened_during_scoring": False,
        "limitations": [
            "Satu evaluator tidak menyediakan estimasi inter-rater agreement.",
            "Evaluator memahami tujuan umum penelitian meski identitas mode dan jarak disembunyikan.",
            "Skor visual adalah audit teknis, bukan UAT atau bukti manfaat pengguna.",
        ],
    }
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return lock


def main() -> None:
    parser = argparse.ArgumentParser(description="Terapkan dan kunci skor evaluasi visual blind v2.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/captures/dataset_visual_evaluation_v2_fresh.csv"),
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("results/captures/dataset_visual_evaluation_score_lock_v2_fresh.json"),
    )
    args = parser.parse_args()
    lock = apply_scores(args.input, args.lock)
    print(json.dumps(lock, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
