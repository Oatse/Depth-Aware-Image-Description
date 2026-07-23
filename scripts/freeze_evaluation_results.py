import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from models.gemma_client import DEFAULT_GEMMA_PROMPT


DEFAULT_ARTIFACT_PATHS = (
    "results/captures/dataset_manifest_v2.json",
    "results/captures/dataset_manifest_v2_validation.json",
    "results/captures/dataset_analysis_rows_v2.csv",
    "results/captures/dataset_analysis_summary_v2.json",
    "results/captures/dataset_visual_scores_v2.csv",
    "results/captures/dataset_visual_summary_v2.json",
    "docs/hasil_sementara_penelitian_v2_20260723.md",
    "docs/dataset_v2_final_evaluation_20260723.md",
)


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


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object wajib tersedia: {path}")
    return value


def _load_runs(path: Path) -> dict[str, dict[str, Any]]:
    runs: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        run = json.loads(line)
        run_id = str(run.get("analysis_run_id") or "")
        if not run_id:
            continue
        if run_id in runs:
            raise ValueError(f"analysis_run_id duplikat pada baris {line_number}: {run_id}")
        runs[run_id] = run
    return runs


def _load_csv_by_capture(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        capture_id = str(row.get("capture_id") or "")
        if not capture_id or capture_id in result:
            raise ValueError(f"capture_id kosong/duplikat pada {path}: {capture_id}")
        result[capture_id] = row
    return result


def _artifact_entry(project_root: Path, relative_path: str) -> dict[str, Any]:
    path = project_root / relative_path
    if not path.is_file():
        raise ValueError(f"Artefak evaluasi tidak ditemukan: {relative_path}")
    data = path.read_bytes()
    return {
        "path": Path(relative_path).as_posix(),
        "size_bytes": len(data),
        "sha256": _sha256_bytes(data),
    }


def build_evaluation_manifest(
    project_root: Path,
    *,
    evaluation_id: str,
    model_id: str,
    dataset_manifest_path: str = "results/captures/dataset_manifest_v2.json",
    captures_root: str = "results/captures",
    analysis_runs_path: str = "results/analysis_runs.jsonl",
    analysis_rows_path: str = "results/captures/dataset_analysis_rows_v2.csv",
    visual_scores_path: str = "results/captures/dataset_visual_scores_v2.csv",
    artifact_paths: tuple[str, ...] = DEFAULT_ARTIFACT_PATHS,
    expected_capture_count: int = 18,
) -> dict[str, Any]:
    dataset_manifest = _read_json(project_root / dataset_manifest_path)
    dataset_rows = dataset_manifest.get("captures") or []
    if len(dataset_rows) != expected_capture_count:
        raise ValueError(
            f"Jumlah capture dataset tidak sesuai: {len(dataset_rows)} != {expected_capture_count}"
        )
    runs = _load_runs(project_root / analysis_runs_path)
    analysis_rows = _load_csv_by_capture(project_root / analysis_rows_path)
    visual_scores = _load_csv_by_capture(project_root / visual_scores_path)

    capture_entries: list[dict[str, Any]] = []
    run_ids: set[str] = set()
    calibration_versions: set[str] = set()
    for dataset_row in dataset_rows:
        capture_id = str(dataset_row["capture_id"])
        record = _read_json(project_root / captures_root / "records" / f"{capture_id}.json")
        if record.get("status") != "completed":
            raise ValueError(f"Capture belum completed: {capture_id}")
        run_id = str(record.get("analysis_run_id") or "")
        if not run_id or run_id in run_ids:
            raise ValueError(f"analysis_run_id kosong/duplikat: {capture_id} -> {run_id}")
        run_ids.add(run_id)
        run = runs.get(run_id)
        if run is None or run.get("capture_id") != capture_id:
            raise ValueError(f"Run tidak ditemukan atau capture_id tidak cocok: {capture_id}")
        output = (run.get("outputs") or {}).get("sensor_assisted") or {}
        if not output.get("success") or output.get("mode") != "sensor_assisted":
            raise ValueError(f"Output sensor_assisted tidak valid: {capture_id}")
        if output.get("mock", {}).get("gemma") is not False:
            raise ValueError(f"Output Gemma mock/tidak diketahui: {capture_id}")
        contribution = output.get("sensor_contribution") or {}
        calibration_version = str(contribution.get("calibration_version") or "")
        if not calibration_version:
            raise ValueError(f"Versi kalibrasi tidak tersedia: {capture_id}")
        calibration_versions.add(calibration_version)
        run_evidence = run.get("sensor_evidence") or {}
        samples = run_evidence.get("samples") or {}
        sensor_1 = samples.get("sensor_1") or {}
        sensor_2 = samples.get("sensor_2") or {}
        if run_evidence.get("capture_id") != capture_id:
            raise ValueError(f"Snapshot sensor tercampur: {capture_id}")
        if sensor_1.get("distance_cm") != dataset_row.get("sensor_1_cm"):
            raise ValueError(f"Snapshot Sensor 1 tidak cocok: {capture_id}")
        if sensor_2.get("distance_cm") != dataset_row.get("sensor_2_cm"):
            raise ValueError(f"Snapshot Sensor 2 tidak cocok: {capture_id}")

        analysis_row = analysis_rows.get(capture_id)
        visual_score = visual_scores.get(capture_id)
        if analysis_row is None or analysis_row.get("analysis_run_id") != run_id:
            raise ValueError(f"Baris analisis tidak cocok: {capture_id}")
        if visual_score is None:
            raise ValueError(f"Skor visual tidak ditemukan: {capture_id}")

        visual_output = {
            "gemma_description": output.get("gemma_description"),
            "gemma_structured": output.get("gemma_structured"),
            "final_description": output.get("final_description"),
        }
        capture_entries.append({
            "capture_id": capture_id,
            "ground_truth_cm": dataset_row["ground_truth_cm"],
            "repeat_index": dataset_row["repeat_index"],
            "image_sha256": dataset_row["image_sha256"],
            "input_sha256": dataset_row["input_sha256"],
            "analysis_status": record["status"],
            "analysis_attempts": record.get("analysis_attempts"),
            "analysis_run_id": run_id,
            "run_sha256": _canonical_sha256(run),
            "output_sha256": _canonical_sha256(output),
            "visual_output_sha256": _canonical_sha256(visual_output),
            "sensor_snapshot_sha256": _canonical_sha256(run_evidence),
            "visual_score_sha256": _canonical_sha256(visual_score),
            "calibration_version": calibration_version,
            "gemma_mock": False,
            "gemma_ms": (output.get("latency") or {}).get("gemma_ms"),
            "total_ms": (output.get("latency") or {}).get("total_ms"),
        })

    if len(calibration_versions) != 1:
        raise ValueError(f"Versi kalibrasi tidak tunggal: {sorted(calibration_versions)}")

    artifacts = [_artifact_entry(project_root, path) for path in artifact_paths]
    return {
        "schema_version": 1,
        "evaluation_id": evaluation_id,
        "dataset_id": dataset_manifest.get("dataset_id"),
        "batch_id": dataset_manifest.get("batch_id"),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "total_captures": len(capture_entries),
        "execution": {
            "mode": "sensor_assisted",
            "one_capture_per_job": True,
            "sequential_runner": True,
            "completed": len(capture_entries),
            "failed": 0,
            "selected_run_ids_sha256": _canonical_sha256(
                [entry["analysis_run_id"] for entry in capture_entries]
            ),
        },
        "model": {
            "model_id": model_id,
            "model_id_provenance": "project_config_and_visual_evaluation_not_logged_per_run",
            "prompt_source_path": "models/gemma_client.py:DEFAULT_GEMMA_PROMPT",
            "prompt_sha256": _sha256_bytes(DEFAULT_GEMMA_PROMPT.encode("utf-8")),
            "prompt_provenance": "current_source_not_logged_per_run",
            "raw_provider_response_preserved": False,
            "mock": False,
        },
        "calibration": {
            "version": next(iter(calibration_versions)),
            "version_provenance": "sensor_contribution_logged_per_run",
        },
        "mutable_source_logs": {
            "analysis_runs_path": Path(analysis_runs_path).as_posix(),
            "whole_file_checksum_included": False,
            "reason": "Log bersifat append-only dan berisi run di luar dataset; setiap run terpilih dikunci secara kanonik.",
        },
        "captures": capture_entries,
        "artifacts": artifacts,
        "claim_boundaries": [
            "Hasil Gemma dan HC-SR04 dilaporkan terpisah.",
            "Angka sensor bukan jarak ke objek yang dinamai Gemma.",
            "Evaluasi visual dilakukan oleh satu evaluator teknis dan bukan UAT.",
            "Hasil tidak membuktikan keselamatan navigasi atau manfaat pengguna.",
        ],
    }


def validate_evaluation_manifest(
    project_root: Path,
    manifest: dict[str, Any],
    *,
    expected_capture_count: int = 18,
) -> dict[str, Any]:
    captures = manifest.get("captures") or []
    if manifest.get("total_captures") != len(captures) or len(captures) != expected_capture_count:
        raise ValueError(f"Jumlah capture evaluation manifest tidak valid: {len(captures)}")
    expected_prompt_hash = _sha256_bytes(DEFAULT_GEMMA_PROMPT.encode("utf-8"))
    if (manifest.get("model") or {}).get("prompt_sha256") != expected_prompt_hash:
        raise ValueError("Checksum prompt source aktif tidak cocok.")

    for artifact in manifest.get("artifacts") or []:
        actual = _artifact_entry(project_root, str(artifact["path"]))
        if actual != artifact:
            raise ValueError(f"Checksum artefak tidak cocok: {artifact['path']}")

    dataset_artifact = next(
        (
            item for item in manifest["artifacts"]
            if item["path"] == "results/captures/dataset_manifest_v2.json"
        ),
        None,
    )
    if dataset_artifact is None:
        raise ValueError("Dataset manifest tidak tercantum sebagai artefak.")
    dataset_manifest = _read_json(project_root / dataset_artifact["path"])
    dataset_by_id = {
        str(row["capture_id"]): row for row in dataset_manifest.get("captures") or []
    }
    runs = _load_runs(project_root / "results/analysis_runs.jsonl")
    scores = _load_csv_by_capture(
        project_root / "results/captures/dataset_visual_scores_v2.csv"
    )
    capture_ids: set[str] = set()
    run_ids: set[str] = set()
    for entry in captures:
        capture_id = str(entry.get("capture_id") or "")
        run_id = str(entry.get("analysis_run_id") or "")
        if not capture_id or capture_id in capture_ids:
            raise ValueError(f"capture_id kosong/duplikat: {capture_id}")
        if not run_id or run_id in run_ids:
            raise ValueError(f"analysis_run_id kosong/duplikat: {run_id}")
        capture_ids.add(capture_id)
        run_ids.add(run_id)
        dataset_row = dataset_by_id.get(capture_id)
        run = runs.get(run_id)
        if dataset_row is None or run is None or run.get("capture_id") != capture_id:
            raise ValueError(f"Dataset/run tidak cocok: {capture_id}")
        record = _read_json(
            project_root / "results/captures/records" / f"{capture_id}.json"
        )
        if record.get("status") != "completed" or record.get("analysis_run_id") != run_id:
            raise ValueError(f"Record capture tidak cocok: {capture_id}")
        output = (run.get("outputs") or {}).get("sensor_assisted") or {}
        evidence = run.get("sensor_evidence") or {}
        visual_output = {
            "gemma_description": output.get("gemma_description"),
            "gemma_structured": output.get("gemma_structured"),
            "final_description": output.get("final_description"),
        }
        expected_hashes = {
            "image_sha256": dataset_row["image_sha256"],
            "input_sha256": dataset_row["input_sha256"],
            "run_sha256": _canonical_sha256(run),
            "output_sha256": _canonical_sha256(output),
            "visual_output_sha256": _canonical_sha256(visual_output),
            "sensor_snapshot_sha256": _canonical_sha256(evidence),
            "visual_score_sha256": _canonical_sha256(scores[capture_id]),
        }
        for field, expected in expected_hashes.items():
            if entry.get(field) != expected:
                raise ValueError(f"Checksum {field} tidak cocok: {capture_id}")
        samples = evidence.get("samples") or {}
        if evidence.get("capture_id") != capture_id:
            raise ValueError(f"Snapshot capture_id tidak cocok: {capture_id}")
        if (samples.get("sensor_1") or {}).get("distance_cm") != dataset_row["sensor_1_cm"]:
            raise ValueError(f"Nilai Sensor 1 tidak cocok: {capture_id}")
        if (samples.get("sensor_2") or {}).get("distance_cm") != dataset_row["sensor_2_cm"]:
            raise ValueError(f"Nilai Sensor 2 tidak cocok: {capture_id}")

    selected_hash = _canonical_sha256([entry["analysis_run_id"] for entry in captures])
    if (manifest.get("execution") or {}).get("selected_run_ids_sha256") != selected_hash:
        raise ValueError("Checksum urutan analysis_run_id tidak cocok.")
    return {
        "valid": True,
        "evaluation_id": manifest.get("evaluation_id"),
        "dataset_id": manifest.get("dataset_id"),
        "total_captures": len(captures),
        "unique_capture_ids": len(capture_ids),
        "unique_analysis_run_ids": len(run_ids),
        "artifacts_verified": len(manifest.get("artifacts") or []),
        "run_checksums_verified": len(captures),
        "output_checksums_verified": len(captures),
        "sensor_snapshots_verified": len(captures),
        "visual_scores_verified": len(captures),
        "prompt_source_checksum_verified": True,
        "raw_provider_response_preserved": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bekukan hasil evaluasi dataset v2 ke manifest final.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/captures/evaluation_manifest_v2.json"),
    )
    parser.add_argument("--evaluation-id", default="hcsr04-indoor-evaluation-v2-clean")
    parser.add_argument("--model-id", default="google/gemma-4-e2b")
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"Evaluation manifest sudah ada dan tidak akan ditimpa: {args.output}")
    manifest = build_evaluation_manifest(
        args.project_root,
        evaluation_id=args.evaluation_id,
        model_id=args.model_id,
    )
    validation = validate_evaluation_manifest(args.project_root, manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "evaluation_id": manifest["evaluation_id"],
        "total_captures": manifest["total_captures"],
        "validation": validation,
        "output": args.output.as_posix(),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
