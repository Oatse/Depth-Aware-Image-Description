import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_DISTANCES_CM = (30.0, 50.0, 75.0, 100.0, 150.0, 200.0)
MANIFEST_SCHEMA_VERSION = 2


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _immutable_input(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "capture_id": record.get("capture_id"),
        "batch_id": record.get("batch_id"),
        "capture_time_ms": record.get("capture_time_ms"),
        "camera_facing_mode": record.get("camera_facing_mode"),
        "image": record.get("image"),
        "sensor_evidence": record.get("sensor_evidence"),
        "metadata": record.get("metadata"),
    }


def build_manifest(
    captures_root: Path,
    *,
    dataset_id: str,
    batch_id: str | None = None,
    image_path_prefix: str | None = None,
    capture_ids: set[str] | None = None,
    image_output_prefix: str | None = None,
) -> dict[str, Any]:
    records_dir = captures_root / "records"
    rows: list[dict[str, Any]] = []
    seen_capture_ids: set[str] = set()
    seen_distance_repeats: set[tuple[float, int]] = set()

    for record_path in sorted(records_dir.glob("*.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        image = record.get("image") or {}
        image_relative_path = str(image.get("path") or "")
        if batch_id is not None and record.get("batch_id") != batch_id:
            continue
        if image_path_prefix is not None and not image_relative_path.startswith(image_path_prefix):
            continue
        capture_id = str(record["capture_id"])
        if capture_ids is not None and capture_id not in capture_ids:
            continue
        if capture_id in seen_capture_ids:
            raise ValueError(f"Capture ID duplikat: {capture_id}")
        seen_capture_ids.add(capture_id)

        metadata = record.get("metadata") or {}
        ground_truth_cm = metadata.get("ground_truth_cm")
        sensor_face_ground_truth_cm = metadata.get("sensor_face_ground_truth_cm")
        repeat_index = metadata.get("repeat_index")
        if ground_truth_cm is None or sensor_face_ground_truth_cm is None or repeat_index is None:
            raise ValueError(f"Metadata wajib belum lengkap: {capture_id}")

        ground_truth_cm = float(ground_truth_cm)
        sensor_face_ground_truth_cm = float(sensor_face_ground_truth_cm)
        repeat_index = int(repeat_index)
        if ground_truth_cm not in EXPECTED_DISTANCES_CM:
            raise ValueError(f"Jarak tidak termasuk protokol: {capture_id} = {ground_truth_cm:g} cm")
        if repeat_index < 1:
            raise ValueError(f"Repeat harus lebih besar dari nol: {capture_id} = {repeat_index}")
        if abs(sensor_face_ground_truth_cm - (ground_truth_cm - 3.0)) > 1e-9:
            raise ValueError(f"Offset kamera-sensor tidak konsisten: {capture_id}")

        distance_repeat = (ground_truth_cm, repeat_index)
        if distance_repeat in seen_distance_repeats:
            raise ValueError(
                f"Kombinasi jarak/repeat duplikat: {ground_truth_cm:g} cm repeat {repeat_index}"
            )
        seen_distance_repeats.add(distance_repeat)

        sensor_evidence = record.get("sensor_evidence") or {}
        if sensor_evidence.get("status") != "paired":
            raise ValueError(f"Status sensor bukan paired: {capture_id}")
        samples = sensor_evidence.get("samples") or {}
        sensor_1 = samples.get("sensor_1") or {}
        sensor_2 = samples.get("sensor_2") or {}
        for sensor_name, sample in (("sensor_1", sensor_1), ("sensor_2", sensor_2)):
            if sample.get("status") != "ok":
                raise ValueError(f"Status {sensor_name} bukan ok: {capture_id}")
            if not isinstance(sample.get("distance_cm"), (int, float)):
                raise ValueError(f"Nilai {sensor_name} tidak valid: {capture_id}")

        source_image_path = captures_root / image_relative_path
        image_path = source_image_path
        if image_output_prefix is not None:
            output_prefix = _safe_image_prefix(image_output_prefix)
            image_path = captures_root / output_prefix / source_image_path.name
            image_path.parent.mkdir(parents=True, exist_ok=True)
            if image_path.exists() and image_path.read_bytes() != source_image_path.read_bytes():
                raise ValueError(f"File clean sudah berbeda: {image_path}")
            if not image_path.exists():
                shutil.copyfile(source_image_path, image_path)
        if not image_path.is_file():
            raise ValueError(f"Gambar tidak ditemukan: {capture_id} -> {image_relative_path}")

        manifest_image_path = image_path.relative_to(captures_root).as_posix()

        rows.append(
            {
                "capture_id": capture_id,
                "batch_id": record.get("batch_id"),
                "capture_time_ms": record.get("capture_time_ms"),
                "capture_status": record.get("status"),
                "ground_truth_cm": ground_truth_cm,
                "sensor_face_ground_truth_cm": sensor_face_ground_truth_cm,
                "repeat_index": repeat_index,
                "image_name": Path(image_relative_path).name,
                "image_path": manifest_image_path,
                "image_size_bytes": image_path.stat().st_size,
                "image_sha256": _sha256_bytes(image_path.read_bytes()),
                "input_sha256": _canonical_sha256(_immutable_input(record)),
                "sensor_status": sensor_evidence["status"],
                "sensor_1_cm": sensor_1["distance_cm"],
                "sensor_1_status": sensor_1["status"],
                "sensor_2_cm": sensor_2["distance_cm"],
                "sensor_2_status": sensor_2["status"],
                "pair_disagreement_cm": sensor_evidence.get("pair_disagreement_cm"),
            }
        )

    seen_distances = {distance for distance, _ in seen_distance_repeats}
    missing_distances = sorted(set(EXPECTED_DISTANCES_CM) - seen_distances)
    if missing_distances:
        raise ValueError(f"Distribusi dataset tidak lengkap. Jarak yang hilang={missing_distances}")

    rows.sort(key=lambda row: (row["ground_truth_cm"], row["repeat_index"]))
    repeat_counts = {
        f"{distance:g}": sum(row["ground_truth_cm"] == distance for row in rows)
        for distance in EXPECTED_DISTANCES_CM
    }
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "batch_id": batch_id,
        "image_path_prefix": image_output_prefix or image_path_prefix,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "total_captures": len(rows),
        "expected_distances_cm": list(EXPECTED_DISTANCES_CM),
        "expected_repeats_per_distance": None,
        "repeat_counts_by_distance": repeat_counts,
        "captures": rows,
    }


def _safe_image_prefix(prefix: str) -> Path:
    relative = Path(prefix.strip().replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("image_output_prefix tidak valid.")
    if relative.parts[0] != "images" or any(not part.replace("_", "a").replace("-", "a").isalnum() for part in relative.parts):
        raise ValueError("image_output_prefix harus berada di bawah images/.")
    return relative


def _read_capture_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {line.strip() for line in text.splitlines() if line.strip()}
    if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
        return {item for item in parsed if item}
    raise ValueError("File capture IDs harus berupa array JSON atau satu ID per baris.")


def validate_manifest(captures_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    captures = manifest.get("captures")
    if not isinstance(captures, list):
        raise ValueError("Daftar captures tidak tersedia pada manifest.")
    if manifest.get("total_captures") != len(captures) or not captures:
        raise ValueError(f"Jumlah capture manifest tidak valid: {len(captures)}")

    capture_ids: set[str] = set()
    image_paths: set[str] = set()
    image_hashes: set[str] = set()
    distance_repeats: set[tuple[float, int]] = set()
    for row in captures:
        capture_id = str(row.get("capture_id") or "")
        if not capture_id or capture_id in capture_ids:
            raise ValueError(f"Capture ID kosong/duplikat: {capture_id}")
        capture_ids.add(capture_id)

        pair = (float(row["ground_truth_cm"]), int(row["repeat_index"]))
        if pair[0] not in EXPECTED_DISTANCES_CM:
            raise ValueError(f"Jarak tidak termasuk protokol: {pair[0]:g} cm")
        if pair[1] < 1:
            raise ValueError(f"Repeat harus lebih besar dari nol: {pair}")
        if pair in distance_repeats:
            raise ValueError(f"Kombinasi jarak/repeat duplikat: {pair}")
        distance_repeats.add(pair)

        image_relative_path = str(row.get("image_path") or "")
        if not image_relative_path or image_relative_path in image_paths:
            raise ValueError(f"Path gambar kosong/duplikat: {image_relative_path}")
        image_paths.add(image_relative_path)
        image_path = captures_root / image_relative_path
        if not image_path.is_file():
            raise ValueError(f"Gambar tidak ditemukan: {capture_id} -> {image_relative_path}")
        actual_image_hash = _sha256_bytes(image_path.read_bytes())
        if actual_image_hash != row.get("image_sha256"):
            raise ValueError(f"Checksum gambar tidak cocok: {capture_id}")
        if actual_image_hash in image_hashes:
            raise ValueError(f"Konten gambar duplikat: {capture_id}")
        image_hashes.add(actual_image_hash)
        if image_path.stat().st_size != row.get("image_size_bytes"):
            raise ValueError(f"Ukuran gambar tidak cocok: {capture_id}")
        if row.get("image_name") != image_path.name:
            raise ValueError(f"Nama gambar tidak cocok: {capture_id}")

        record_path = captures_root / "records" / f"{capture_id}.json"
        if not record_path.is_file():
            raise ValueError(f"Metadata capture tidak ditemukan: {capture_id}")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if _canonical_sha256(_immutable_input(record)) != row.get("input_sha256"):
            raise ValueError(f"Checksum metadata tidak cocok: {capture_id}")
        metadata = record.get("metadata") or {}
        evidence = record.get("sensor_evidence") or {}
        samples = evidence.get("samples") or {}
        sensor_1 = samples.get("sensor_1") or {}
        sensor_2 = samples.get("sensor_2") or {}
        expected_values = {
            "batch_id": record.get("batch_id"),
            "capture_time_ms": record.get("capture_time_ms"),
            "ground_truth_cm": float(metadata["ground_truth_cm"]),
            "sensor_face_ground_truth_cm": float(metadata["sensor_face_ground_truth_cm"]),
            "repeat_index": int(metadata["repeat_index"]),
            "sensor_status": evidence.get("status"),
            "sensor_1_cm": sensor_1.get("distance_cm"),
            "sensor_1_status": sensor_1.get("status"),
            "sensor_2_cm": sensor_2.get("distance_cm"),
            "sensor_2_status": sensor_2.get("status"),
            "pair_disagreement_cm": evidence.get("pair_disagreement_cm"),
        }
        for field, expected in expected_values.items():
            if row.get(field) != expected:
                raise ValueError(f"Nilai {field} tidak cocok: {capture_id}")
        if (
            evidence.get("status") != "paired"
            or sensor_1.get("status") != "ok"
            or sensor_2.get("status") != "ok"
        ):
            raise ValueError(f"Status sensor tidak sesuai: {capture_id}")

    seen_distances = {distance for distance, _ in distance_repeats}
    if seen_distances != set(EXPECTED_DISTANCES_CM):
        raise ValueError("Distribusi jarak manifest tidak lengkap.")
    repeat_counts = {
        f"{distance:g}": sum(row["ground_truth_cm"] == distance for row in captures)
        for distance in EXPECTED_DISTANCES_CM
    }
    return {
        "valid": True,
        "dataset_id": manifest.get("dataset_id"),
        "total_captures": len(captures),
        "repeat_counts_by_distance": repeat_counts,
        "unique_capture_ids": len(capture_ids),
        "unique_images": len(image_paths),
        "unique_image_checksums": len(image_hashes),
        "sensor_statuses": {
            "paired": len(captures),
            "sensor_1_ok": len(captures),
            "sensor_2_ok": len(captures),
        },
        "checksums_verified": len(captures),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bekukan dataset capture lokal ke manifest JSON.")
    parser.add_argument(
        "--captures-root",
        type=Path,
        default=Path("results/captures"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/captures/dataset_manifest_v2.json"),
    )
    parser.add_argument("--dataset-id", default="hcsr04-indoor-distance-v2-clean")
    parser.add_argument("--batch-id")
    parser.add_argument("--image-path-prefix")
    parser.add_argument("--capture-ids-file", type=Path)
    parser.add_argument("--image-output-prefix")
    args = parser.parse_args()

    if args.output.exists():
        parser.error(f"Manifest sudah ada dan tidak akan ditimpa: {args.output}")
    manifest = build_manifest(
        args.captures_root,
        dataset_id=args.dataset_id,
        batch_id=args.batch_id,
        image_path_prefix=args.image_path_prefix,
        capture_ids=_read_capture_ids(args.capture_ids_file) if args.capture_ids_file else None,
        image_output_prefix=args.image_output_prefix,
    )
    validation = validate_manifest(args.captures_root, manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "dataset_id": manifest["dataset_id"],
        "total_captures": manifest["total_captures"],
        "validation": validation,
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
