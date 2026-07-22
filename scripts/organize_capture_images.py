import csv
import json
from pathlib import Path
from typing import Any


V2_BATCH_ID = "0c9d8d8e-a646-4302-9e1c-696423ebf689"
V1_IMAGE_DIR = "dataset_v1_meteran"
V2_IMAGE_DIR = "dataset_v2_clean"


def _write_json_atomic(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _replace_capture_paths(path: Path, replacements: dict[str, str]) -> None:
    if not path.is_file():
        return
    original = path.read_text(encoding="utf-8")
    updated = original
    for old, new in replacements.items():
        updated = updated.replace(old, new)
    if updated != original:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(updated, encoding="utf-8")
        temporary.replace(path)


def organize_capture_images(program_root: Path) -> dict[str, int]:
    captures_root = program_root / "results" / "captures"
    records_dir = captures_root / "records"
    records: list[tuple[Path, dict[str, Any]]] = []
    for record_path in sorted(records_dir.glob("*.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        records.append((record_path, record))
    if len(records) != 36:
        raise ValueError(f"Migrasi mengharapkan 36 record, ditemukan {len(records)}.")

    v2_count = sum(record.get("batch_id") == V2_BATCH_ID for _, record in records)
    if v2_count != 18:
        raise ValueError(f"Dataset v2 harus berisi 18 record, ditemukan {v2_count}.")

    replacements: dict[str, str] = {}
    moved = {"v1": 0, "v2": 0}
    for record_path, record in records:
        capture_id = str(record["capture_id"])
        old_relative = Path(str(record["image"]["path"]))
        dataset_dir = V2_IMAGE_DIR if record.get("batch_id") == V2_BATCH_ID else V1_IMAGE_DIR
        new_relative = Path("images") / dataset_dir / old_relative.name
        old_path = captures_root / old_relative
        new_path = captures_root / new_relative
        if not old_path.is_file():
            raise ValueError(f"Gambar sumber tidak ditemukan: {old_path}")
        if new_path.exists():
            raise ValueError(f"Target gambar sudah ada: {new_path}")
        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.replace(new_path)
        record["image"]["path"] = new_relative.as_posix()
        _write_json_atomic(record_path, record)

        old_fragment = f"captures/images/{capture_id}{old_path.suffix}"
        new_fragment = f"captures/{new_relative.as_posix()}"
        replacements[old_fragment] = new_fragment
        replacements[old_relative.as_posix()] = new_relative.as_posix()
        moved["v2" if dataset_dir == V2_IMAGE_DIR else "v1"] += 1

    manifest_path = captures_root / "dataset_manifest_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    v1_paths = {
        record["capture_id"]: record["image"]["path"]
        for _, record in records
        if record.get("batch_id") != V2_BATCH_ID
    }
    for entry in manifest["captures"]:
        entry["image_path"] = v1_paths[str(entry["capture_id"])]
    _write_json_atomic(manifest_path, manifest)

    visual_template = captures_root / "dataset_visual_evaluation_template_v1.csv"
    if visual_template.is_file():
        with visual_template.open("r", encoding="utf-8-sig", newline="") as source:
            rows = list(csv.DictReader(source))
            fieldnames = list(rows[0]) if rows else []
        for row in rows:
            row["image_path"] = v1_paths[row["capture_id"]]
        temporary = visual_template.with_suffix(".csv.tmp")
        with temporary.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(visual_template)

    for artifact in (
        program_root / "results" / "analysis_runs.jsonl",
        program_root / "results" / "predictions.csv",
    ):
        _replace_capture_paths(artifact, replacements)
    return moved


def main() -> None:
    program_root = Path(__file__).resolve().parents[1]
    moved = organize_capture_images(program_root)
    print(json.dumps({"moved": moved}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
