import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from statistics import fmean
from typing import Any


ANALYSIS_FIELDS = (
    "capture_id",
    "ground_truth_cm",
    "repeat_index",
    "image_path",
    "image_sha256",
    "mode",
    "analysis_run_id",
    "model_id",
    "prompt_kind",
    "prompt_sha256",
    "request_started_at",
    "main_object",
    "closest_object",
    "object_position",
    "objects",
    "obstacle_candidate",
    "gemma_description",
    "final_description",
    "sensor_status",
    "sensor_1_cm",
    "sensor_2_cm",
    "frontal_reference_cm",
    "gemma_ms",
    "total_ms",
    "run_sha256",
    "output_sha256",
)

VISUAL_FIELDS = (
    "evaluation_item_id",
    "image_path",
    "main_object",
    "closest_object",
    "object_position",
    "gemma_description",
    "manual_review_status",
    "object_consistency",
    "spatial_consistency",
    "clarity",
    "naturalness",
    "scene_completeness",
    "unsupported_claims",
    "evaluator_notes",
)

VISUAL_KEY_FIELDS = (
    "evaluation_item_id",
    "capture_id",
    "ground_truth_cm",
    "repeat_index",
    "mode",
    "model_id",
    "analysis_run_id",
    "prompt_kind",
    "source_image_path",
    "blind_image_path",
    "source_image_sha256",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object wajib tersedia: {path}")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(encoded)


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


def _error_metrics(errors: list[float]) -> dict[str, float | int]:
    if not errors:
        raise ValueError("Daftar error sensor kosong.")
    return {
        "n": len(errors),
        "bias_cm": round(fmean(errors), 4),
        "mae_cm": round(fmean(abs(error) for error in errors), 4),
        "rmse_cm": round(sqrt(fmean(error * error for error in errors)), 4),
        "max_abs_error_cm": round(max(abs(error) for error in errors), 4),
    }


def _selection_by_capture(path: Path, expected_mode: str) -> dict[str, str]:
    selection = _read_json(path)
    if selection.get("mode") != expected_mode:
        raise ValueError(f"Mode run selection tidak cocok: {path}")
    result: dict[str, str] = {}
    for entry in selection.get("runs") or []:
        capture_id = str(entry.get("capture_id") or "")
        run_id = str(entry.get("analysis_run_id") or "")
        if not capture_id or not run_id or capture_id in result:
            raise ValueError(f"Run selection tidak valid: {path} -> {capture_id}")
        result[capture_id] = run_id
    return result


def build_reports(
    manifest_path: Path,
    analysis_runs_path: Path,
    selections: dict[str, Path],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    manifest = _read_json(manifest_path)
    captures = manifest.get("captures") or []
    if not captures:
        raise ValueError("Manifest tidak memuat capture.")
    runs = _load_runs(analysis_runs_path)
    selection_maps = {
        mode: _selection_by_capture(path, mode)
        for mode, path in selections.items()
    }
    expected_capture_ids = [str(entry["capture_id"]) for entry in captures]
    for mode, mapping in selection_maps.items():
        if set(mapping) != set(expected_capture_ids):
            raise ValueError(f"Capture run selection {mode} tidak sama dengan manifest.")

    rows: list[dict[str, Any]] = []
    selected_run_ids: set[str] = set()
    for capture in captures:
        capture_id = str(capture["capture_id"])
        for mode in ("gemma_only", "sensor_assisted"):
            run_id = selection_maps[mode][capture_id]
            if run_id in selected_run_ids:
                raise ValueError(f"Run dipakai lebih dari sekali: {run_id}")
            selected_run_ids.add(run_id)
            run = runs.get(run_id)
            if run is None or run.get("capture_id") != capture_id:
                raise ValueError(f"Run tidak ditemukan atau capture_id mismatch: {run_id}")
            output = (run.get("outputs") or {}).get(mode) or {}
            if output.get("success") is not True or output.get("mode") != mode:
                raise ValueError(f"Output {mode} gagal/tidak valid: {capture_id}")
            provenance = output.get("gemma_provenance") or {}
            prompt = str(provenance.get("prompt") or "")
            prompt_sha256 = str(provenance.get("prompt_sha256") or "")
            if not prompt or _sha256_bytes(prompt.encode("utf-8")) != prompt_sha256:
                raise ValueError(f"Prompt provenance tidak valid: {capture_id} {mode}")
            prompt_kind = (
                "sensor_conditioned"
                if prompt.startswith("Konteks sensor terverifikasi:")
                else "default_visual"
            )
            expected_prompt_kind = (
                "sensor_conditioned" if mode == "sensor_assisted" else "default_visual"
            )
            if prompt_kind != expected_prompt_kind:
                raise ValueError(f"Jenis prompt tidak cocok: {capture_id} {mode}")

            structured = output.get("gemma_structured") or {}
            description = str(output.get("gemma_description") or "")
            main_object = str(structured.get("main_object") or "")
            objects = structured.get("objects") or []
            contribution = output.get("sensor_contribution") or {}
            if mode == "sensor_assisted":
                if contribution.get("status") != "applied":
                    raise ValueError(f"Sensor tidak applied: {capture_id}")
                evidence = run.get("sensor_evidence") or {}
                samples = evidence.get("samples") or {}
                if evidence.get("capture_id") != capture_id:
                    raise ValueError(f"Snapshot sensor capture_id mismatch: {capture_id}")
                if (samples.get("sensor_1") or {}).get("distance_cm") != capture.get("sensor_1_cm"):
                    raise ValueError(f"Snapshot Sensor 1 mismatch: {capture_id}")
                if (samples.get("sensor_2") or {}).get("distance_cm") != capture.get("sensor_2_cm"):
                    raise ValueError(f"Snapshot Sensor 2 mismatch: {capture_id}")
            elif output.get("sensor_contribution") is not None:
                raise ValueError(f"Gemma-only memuat kontribusi sensor: {capture_id}")

            latency = output.get("latency") or {}
            rows.append({
                "capture_id": capture_id,
                "ground_truth_cm": float(capture["ground_truth_cm"]),
                "repeat_index": int(capture["repeat_index"]),
                "image_path": capture["image_path"],
                "image_sha256": capture["image_sha256"],
                "mode": mode,
                "analysis_run_id": run_id,
                "model_id": provenance.get("model_id"),
                "prompt_kind": prompt_kind,
                "prompt_sha256": prompt_sha256,
                "request_started_at": provenance.get("request_started_at"),
                "main_object": main_object,
                "closest_object": structured.get("closest_object"),
                "object_position": structured.get("object_position"),
                "objects": json.dumps(objects, ensure_ascii=False),
                "obstacle_candidate": structured.get("obstacle_candidate"),
                "gemma_description": description,
                "final_description": output.get("final_description"),
                "sensor_status": contribution.get("status") if contribution else "not_applicable",
                "sensor_1_cm": contribution.get("sensor_1_cm"),
                "sensor_2_cm": contribution.get("sensor_2_cm"),
                "frontal_reference_cm": contribution.get("frontal_reference_cm"),
                "gemma_ms": latency.get("gemma_ms"),
                "total_ms": latency.get("total_ms"),
                "run_sha256": _canonical_sha256(run),
                "output_sha256": _canonical_sha256(output),
            })

    summaries: dict[str, Any] = {}
    for mode in ("gemma_only", "sensor_assisted"):
        mode_rows = [row for row in rows if row["mode"] == mode]
        by_distance = []
        for distance in sorted({row["ground_truth_cm"] for row in mode_rows}):
            group = [row for row in mode_rows if row["ground_truth_cm"] == distance]
            by_distance.append({
                "ground_truth_cm": distance,
                "n": len(group),
                "main_object_nonempty_count": sum(bool(str(row["main_object"]).strip()) for row in group),
                "description_nonempty_count": sum(
                    bool(str(row["gemma_description"]).strip()) for row in group
                ),
                "mean_total_latency_ms": round(fmean(float(row["total_ms"]) for row in group), 2),
            })
        summaries[mode] = {
            "mode": mode,
            "completed": len(mode_rows),
            "failed": 0,
            "main_object_nonempty_count": sum(
                bool(str(row["main_object"]).strip()) for row in mode_rows
            ),
            "description_nonempty_count": sum(
                bool(str(row["gemma_description"]).strip()) for row in mode_rows
            ),
            "mean_total_latency_ms": round(fmean(float(row["total_ms"]) for row in mode_rows), 2),
            "by_distance": by_distance,
        }

    comparison_rows: list[dict[str, Any]] = []
    for capture in captures:
        capture_id = str(capture["capture_id"])
        gemma_row = next(row for row in rows if row["capture_id"] == capture_id and row["mode"] == "gemma_only")
        sensor_row = next(row for row in rows if row["capture_id"] == capture_id and row["mode"] == "sensor_assisted")
        comparison_rows.append({
            "capture_id": capture_id,
            "ground_truth_cm": float(capture["ground_truth_cm"]),
            "repeat_index": int(capture["repeat_index"]),
            "gemma_only_main_object": gemma_row["main_object"],
            "sensor_assisted_main_object": sensor_row["main_object"],
            "gemma_only_description": gemma_row["gemma_description"],
            "sensor_assisted_description": sensor_row["gemma_description"],
            "main_object_text_equal": int(
                gemma_row["main_object"] == sensor_row["main_object"]
            ),
            "description_text_equal": int(
                gemma_row["gemma_description"] == sensor_row["gemma_description"]
            ),
        })

    sensor_rows = [row for row in rows if row["mode"] == "sensor_assisted"]
    sensor_1_errors = [
        float(row["sensor_1_cm"]) - (float(row["ground_truth_cm"]) - 3.0)
        for row in sensor_rows
    ]
    sensor_2_errors = [
        float(row["sensor_2_cm"]) - (float(row["ground_truth_cm"]) - 3.0)
        for row in sensor_rows
    ]
    frontal_errors = [
        float(row["frontal_reference_cm"]) - float(row["ground_truth_cm"])
        for row in sensor_rows
    ]
    pair_disagreements = [
        abs(float(row["sensor_1_cm"]) - float(row["sensor_2_cm"]))
        for row in sensor_rows
    ]
    sensor_metrics = {
        "reference_definition": {
            "raw_sensor_error": "sensor_raw_cm - (ground_truth_cm - 3.0)",
            "corrected_frontal_error": "frontal_reference_cm - ground_truth_cm",
        },
        "sensor_1_raw": _error_metrics(sensor_1_errors),
        "sensor_2_raw": _error_metrics(sensor_2_errors),
        "corrected_frontal_reference": _error_metrics(frontal_errors),
        "pair_disagreement_cm": {
            "mean": round(fmean(pair_disagreements), 4),
            "max": round(max(pair_disagreements), 4),
        },
    }

    comparison_summary = {
        "schema_version": 1,
        "dataset_id": manifest.get("dataset_id"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_type": "technical_dual_mode_output_audit",
        "definition": (
            "Audit teknis netral atas kelengkapan output, latency, provenance, "
            "perbedaan teks antarmode, dan error referensi sensor."
        ),
        "total_images": len(captures),
        "total_runs": len(rows),
        "modes": summaries,
        "sensor_metrics": sensor_metrics,
        "mode_comparison": {
            "main_object_text_changed_count": sum(
                not row["main_object_text_equal"] for row in comparison_rows
            ),
            "description_text_changed_count": sum(
                not row["description_text_equal"] for row in comparison_rows
            ),
            "interpretation": (
                "Perbedaan teks menunjukkan output antarmode berubah, bukan bukti "
                "bahwa salah satu mode lebih benar."
            ),
        },
        "limitations": [
            "Kelengkapan field dan perbedaan teks tidak membuktikan kebenaran semantik.",
            "Kualitas visual memerlukan penilaian blind terhadap citra tanpa membuka mode atau target.",
            "Template evaluasi visual aktif belum berisi skor evaluator manusia dan bukan UAT.",
            "Inferensi tidak memakai seed sehingga hasil byte-for-byte tidak dijamin berulang.",
        ],
    }
    return rows, comparison_summary, comparison_rows, manifest


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def build_blinded_visual_rows(
    rows: list[dict[str, Any]],
    *,
    dataset_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    randomized = sorted(
        rows,
        key=lambda row: _sha256_bytes(
            (
                f"{dataset_id}:{row['analysis_run_id']}:"
                "visual-evaluation-blind-v1"
            ).encode("utf-8")
        ),
    )
    visual_rows: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []
    for index, row in enumerate(randomized, 1):
        evaluation_item_id = f"VE-{index:03d}"
        source_image_path = str(row["image_path"])
        suffix = Path(source_image_path).suffix.lower() or ".jpg"
        blind_image_path = (
            f"images/visual_evaluation_blind_v2/{evaluation_item_id}{suffix}"
        )
        visual_rows.append({
            "evaluation_item_id": evaluation_item_id,
            "image_path": blind_image_path,
            "main_object": row["main_object"],
            "closest_object": row["closest_object"],
            "object_position": row["object_position"],
            "gemma_description": row["gemma_description"],
            "manual_review_status": "pending",
        })
        key_rows.append({
            "evaluation_item_id": evaluation_item_id,
            "capture_id": row["capture_id"],
            "ground_truth_cm": row["ground_truth_cm"],
            "repeat_index": row["repeat_index"],
            "mode": row["mode"],
            "model_id": row["model_id"],
            "analysis_run_id": row["analysis_run_id"],
            "prompt_kind": row["prompt_kind"],
            "source_image_path": source_image_path,
            "blind_image_path": blind_image_path,
            "source_image_sha256": row["image_sha256"],
        })
    return visual_rows, key_rows


def write_reports(
    output_dir: Path,
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = output_dir / "dataset_analysis_rows_v2_fresh.csv"
    summary_path = output_dir / "dataset_analysis_summary_v2_fresh.json"
    visual_path = output_dir / "dataset_visual_evaluation_v2_fresh.csv"
    visual_key_path = output_dir / "dataset_visual_evaluation_key_v2_fresh.csv"
    visual_image_manifest_path = (
        output_dir / "dataset_visual_evaluation_blind_images_v2_fresh.json"
    )
    comparison_path = output_dir / "dataset_mode_comparison_v2_fresh.csv"
    evaluation_manifest_path = output_dir / "evaluation_manifest_v2_fresh.json"

    _write_csv(analysis_path, ANALYSIS_FIELDS, rows)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    visual_rows, visual_key_rows = build_blinded_visual_rows(
        rows,
        dataset_id=str(manifest.get("dataset_id") or ""),
    )
    blind_image_entries = []
    for key_row in visual_key_rows:
        source_path = output_dir / str(key_row["source_image_path"])
        blind_path = output_dir / str(key_row["blind_image_path"])
        source_bytes = source_path.read_bytes()
        source_sha256 = _sha256_bytes(source_bytes)
        if source_sha256 != key_row["source_image_sha256"]:
            raise ValueError(
                f"Checksum sumber gambar blind tidak cocok: {source_path}"
            )
        blind_path.parent.mkdir(parents=True, exist_ok=True)
        blind_path.write_bytes(source_bytes)
        blind_image_entries.append({
            "evaluation_item_id": key_row["evaluation_item_id"],
            "blind_image_path": key_row["blind_image_path"],
            "size_bytes": len(source_bytes),
            "sha256": source_sha256,
        })
    visual_image_manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": manifest.get("dataset_id"),
                "item_count": len(blind_image_entries),
                "images": blind_image_entries,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_csv(visual_path, VISUAL_FIELDS, visual_rows)
    _write_csv(visual_key_path, VISUAL_KEY_FIELDS, visual_key_rows)
    comparison_fields = tuple(comparison_rows[0])
    _write_csv(comparison_path, comparison_fields, comparison_rows)

    artifact_paths = (
        source_paths["manifest"],
        source_paths["manifest"].with_name("dataset_manifest_v2_fresh_validation.json"),
        analysis_path,
        summary_path,
        visual_path,
        visual_key_path,
        visual_image_manifest_path,
        comparison_path,
        output_dir / "dataset_v2_fresh_reanalysis_report.md",
        Path("docs/dataset_v2_final_evaluation_20260723.md"),
    )
    artifact_paths = tuple(path for path in artifact_paths if path.is_file())
    evaluation_manifest = {
        "schema_version": 1,
        "evaluation_id": "dataset-v2-fresh-dual-mode-20260723",
        "dataset_id": manifest.get("dataset_id"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_manifest_sha256": _sha256_bytes(source_paths["manifest"].read_bytes()),
        "analysis_runs": {
            "path": source_paths["analysis_runs"].as_posix(),
            "whole_log_checksum_included": False,
            "selected_run_count": len(rows),
        },
        "run_selections": {
            mode: {
                "path": path.as_posix(),
                "sha256": _sha256_bytes(path.read_bytes()),
            }
            for mode, path in source_paths.items()
            if mode in {"gemma_only", "sensor_assisted"}
        },
        "visual_evaluation_blinding": {
            "template_path": visual_path.as_posix(),
            "key_path": visual_key_path.as_posix(),
            "blind_image_manifest_path": visual_image_manifest_path.as_posix(),
            "item_count": len(visual_rows),
            "ordering": "deterministic_sha256_pseudorandom",
            "withhold_key_from_evaluator": True,
            "hidden_from_template": [
                "capture_id",
                "ground_truth_cm",
                "repeat_index",
                "mode",
                "model_id",
                "analysis_run_id",
                "prompt_kind",
                "source_image_path",
                "source_image_sha256",
            ],
        },
        "selected_runs": [
            {
                "capture_id": row["capture_id"],
                "mode": row["mode"],
                "analysis_run_id": row["analysis_run_id"],
                "prompt_sha256": row["prompt_sha256"],
                "run_sha256": row["run_sha256"],
                "output_sha256": row["output_sha256"],
            }
            for row in rows
        ],
        "artifacts": [
            {
                "path": path.as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_bytes(path.read_bytes()),
            }
            for path in artifact_paths
        ],
        "claim_boundaries": summary["limitations"],
    }
    evaluation_manifest_path.write_text(
        json.dumps(evaluation_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    selected_runs = evaluation_manifest["selected_runs"]
    selected_capture_ids = {str(row["capture_id"]) for row in selected_runs}
    selected_run_ids = {str(row["analysis_run_id"]) for row in selected_runs}
    selected_modes = {
        mode: sum(row["mode"] == mode for row in selected_runs)
        for mode in ("gemma_only", "sensor_assisted")
    }
    visual_ids = {str(row["evaluation_item_id"]) for row in visual_rows}
    visual_key_ids = {str(row["evaluation_item_id"]) for row in visual_key_rows}
    blind_image_ids = {
        str(row["evaluation_item_id"]) for row in blind_image_entries
    }
    for blind_image in blind_image_entries:
        blind_path = output_dir / str(blind_image["blind_image_path"])
        if (
            not blind_path.is_file()
            or blind_path.stat().st_size != blind_image["size_bytes"]
            or _sha256_bytes(blind_path.read_bytes()) != blind_image["sha256"]
        ):
            raise ValueError(f"Gambar evaluasi blind tidak valid: {blind_path}")
    for artifact in evaluation_manifest["artifacts"]:
        artifact_path = Path(str(artifact["path"]))
        if (
            not artifact_path.is_file()
            or artifact_path.stat().st_size != artifact["size_bytes"]
            or _sha256_bytes(artifact_path.read_bytes()) != artifact["sha256"]
        ):
            raise ValueError(f"Artefak evaluation manifest tidak valid: {artifact_path}")
    validation = {
        "valid": True,
        "evaluation_id": evaluation_manifest["evaluation_id"],
        "dataset_id": evaluation_manifest["dataset_id"],
        "input_manifest_checksum_verified": (
            _sha256_bytes(source_paths["manifest"].read_bytes())
            == evaluation_manifest["input_manifest_sha256"]
        ),
        "selected_run_count": len(selected_runs),
        "unique_selected_run_ids": len(selected_run_ids),
        "unique_capture_ids": len(selected_capture_ids),
        "selected_modes": selected_modes,
        "visual_evaluation_blind": {
            "template_rows": len(visual_rows),
            "key_rows": len(visual_key_rows),
            "unique_item_ids": len(visual_ids),
            "template_key_ids_match": visual_ids == visual_key_ids,
            "blind_image_count": len(blind_image_ids),
            "template_blind_image_ids_match": visual_ids == blind_image_ids,
            "withhold_key_from_evaluator": True,
        },
        "artifact_checksums_verified": len(evaluation_manifest["artifacts"]),
    }
    if (
        not validation["input_manifest_checksum_verified"]
        or len(selected_runs) != len(rows)
        or len(selected_run_ids) != len(rows)
        or len(selected_capture_ids) != len(manifest["captures"])
        or any(count != len(manifest["captures"]) for count in selected_modes.values())
        or len(visual_ids) != len(rows)
        or visual_ids != visual_key_ids
        or visual_ids != blind_image_ids
    ):
        raise ValueError("Evaluation manifest fresh tidak lolos validasi.")
    evaluation_validation_path = output_dir / "evaluation_manifest_v2_fresh_validation.json"
    evaluation_validation_path.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "analysis": analysis_path.as_posix(),
        "summary": summary_path.as_posix(),
        "visual_evaluation": visual_path.as_posix(),
        "visual_evaluation_key": visual_key_path.as_posix(),
        "visual_evaluation_blind_images": visual_image_manifest_path.as_posix(),
        "mode_comparison": comparison_path.as_posix(),
        "evaluation_manifest": evaluation_manifest_path.as_posix(),
        "evaluation_manifest_validation": evaluation_validation_path.as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bangun laporan fresh dua mode dari run ID yang dibekukan.")
    parser.add_argument("--manifest", type=Path, default=Path("results/captures/dataset_manifest_v2.json"))
    parser.add_argument("--analysis-runs", type=Path, default=Path("results/analysis_runs.jsonl"))
    parser.add_argument(
        "--gemma-selection",
        type=Path,
        default=Path("results/captures/fresh_run_selection_gemma_only_v2.json"),
    )
    parser.add_argument(
        "--sensor-selection",
        type=Path,
        default=Path("results/captures/fresh_run_selection_sensor_assisted_v2.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results/captures"))
    args = parser.parse_args()
    selections = {
        "gemma_only": args.gemma_selection,
        "sensor_assisted": args.sensor_selection,
    }
    rows, summary, comparison_rows, manifest = build_reports(
        args.manifest,
        args.analysis_runs,
        selections,
    )
    outputs = write_reports(
        args.output_dir,
        rows,
        summary,
        comparison_rows,
        manifest,
        {
            "manifest": args.manifest,
            "analysis_runs": args.analysis_runs,
            **selections,
        },
    )
    print(json.dumps({
        "total_images": summary["total_images"],
        "total_runs": summary["total_runs"],
        "modes": summary["modes"],
        "mode_comparison": summary["mode_comparison"],
        "outputs": outputs,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
