import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_DISTANCES_CM = (30.0, 50.0, 75.0, 100.0, 150.0, 200.0)
EXPECTED_REPEATS = (1, 2, 3)


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


def build_manifest(captures_root: Path, *, dataset_id: str) -> dict[str, Any]:
    records_dir = captures_root / "records"
    rows: list[dict[str, Any]] = []
    seen_capture_ids: set[str] = set()
    seen_distance_repeats: set[tuple[float, int]] = set()

    for record_path in sorted(records_dir.glob("*.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        capture_id = str(record["capture_id"])
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
        if repeat_index not in EXPECTED_REPEATS:
            raise ValueError(f"Repeat tidak valid: {capture_id} = {repeat_index}")
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

        image = record.get("image") or {}
        image_relative_path = str(image["path"])
        image_path = captures_root / image_relative_path
        if not image_path.is_file():
            raise ValueError(f"Gambar tidak ditemukan: {capture_id} -> {image_relative_path}")

        immutable_input = {
            "capture_id": capture_id,
            "batch_id": record.get("batch_id"),
            "capture_time_ms": record.get("capture_time_ms"),
            "camera_facing_mode": record.get("camera_facing_mode"),
            "mode": record.get("mode"),
            "image": image,
            "sensor_evidence": sensor_evidence,
            "metadata": metadata,
        }
        samples = sensor_evidence.get("samples") or {}
        rows.append(
            {
                "capture_id": capture_id,
                "ground_truth_cm": ground_truth_cm,
                "sensor_face_ground_truth_cm": sensor_face_ground_truth_cm,
                "repeat_index": repeat_index,
                "image_path": image_relative_path,
                "image_size_bytes": image_path.stat().st_size,
                "image_sha256": _sha256_bytes(image_path.read_bytes()),
                "input_sha256": _canonical_sha256(immutable_input),
                "sensor_status": sensor_evidence["status"],
                "sensor_1_cm": (samples.get("sensor_1") or {}).get("distance_cm"),
                "sensor_2_cm": (samples.get("sensor_2") or {}).get("distance_cm"),
                "pair_disagreement_cm": sensor_evidence.get("pair_disagreement_cm"),
            }
        )

    expected_pairs = {
        (distance, repeat)
        for distance in EXPECTED_DISTANCES_CM
        for repeat in EXPECTED_REPEATS
    }
    if seen_distance_repeats != expected_pairs:
        missing = sorted(expected_pairs - seen_distance_repeats)
        extra = sorted(seen_distance_repeats - expected_pairs)
        raise ValueError(f"Distribusi dataset tidak lengkap. missing={missing}, extra={extra}")

    rows.sort(key=lambda row: (row["ground_truth_cm"], row["repeat_index"]))
    return {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "total_captures": len(rows),
        "expected_distances_cm": list(EXPECTED_DISTANCES_CM),
        "expected_repeats_per_distance": len(EXPECTED_REPEATS),
        "captures": rows,
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
        default=Path("results/captures/dataset_manifest_v1.json"),
    )
    parser.add_argument("--dataset-id", default="hcsr04-indoor-distance-v1")
    args = parser.parse_args()

    if args.output.exists():
        parser.error(f"Manifest sudah ada dan tidak akan ditimpa: {args.output}")
    manifest = build_manifest(args.captures_root, dataset_id=args.dataset_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "dataset_id": manifest["dataset_id"],
        "total_captures": manifest["total_captures"],
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
