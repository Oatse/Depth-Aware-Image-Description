import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.freeze_capture_dataset import validate_manifest


PRIMARY_ARTIFACTS = (
    "results/captures/README.md",
    "results/captures/dataset_manifest_v2.json",
    "results/captures/dataset_manifest_v2_fresh_validation.json",
    "results/captures/dataset_selected_analysis_runs_v2_fresh.jsonl",
    "results/captures/fresh_run_selection_gemma_only_v2.json",
    "results/captures/fresh_run_selection_sensor_assisted_v2.json",
    "results/captures/dataset_analysis_rows_v2_fresh.csv",
    "results/captures/dataset_analysis_summary_v2_fresh.json",
    "results/captures/dataset_mode_comparison_v2_fresh.csv",
    "results/captures/dataset_visual_evaluation_v2_fresh.csv",
    "results/captures/dataset_visual_evaluation_key_v2_fresh.csv",
    "results/captures/dataset_visual_evaluation_blind_images_v2_fresh.json",
    "results/captures/dataset_visual_evaluation_score_lock_v2_fresh.json",
    "results/captures/dataset_visual_summary_v2_fresh.json",
    "results/captures/dataset_visual_paired_comparison_v2_fresh.csv",
    "results/captures/dataset_v2_reanalysis_final_report_20260723.md",
    "CONTEXT.md",
    "instructions/PROJECT_INITIALIZATION.md",
    "docs/architecture.md",
    "docs/evaluation_protocol.md",
    "docs/dataset_v2_final_evaluation_20260723.md",
    "scripts/freeze_capture_dataset.py",
    "scripts/analyze_saved_captures.py",
    "scripts/build_fresh_dataset_reports.py",
    "scripts/build_visual_review_contact_sheets.py",
    "scripts/apply_blind_visual_scores_v2.py",
    "scripts/summarize_blind_visual_scores_v2.py",
    "scripts/finalize_dataset_v2_evaluation.py",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _load_runs(path: Path) -> dict[str, dict[str, Any]]:
    runs: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        run = json.loads(line)
        run_id = str(run.get("analysis_run_id") or "")
        if run_id:
            runs[run_id] = run
    return runs


def _load_or_freeze_selected_runs(
    snapshot_path: Path,
    runtime_log_path: Path,
    selected_run_ids: set[str],
) -> dict[str, dict[str, Any]]:
    if not snapshot_path.exists():
        runtime_runs = _load_runs(runtime_log_path)
        missing = selected_run_ids - set(runtime_runs)
        if missing:
            raise ValueError(f"Run final tidak ditemukan: {sorted(missing)}")
        snapshot_path.write_text(
            "\n".join(
                json.dumps(runtime_runs[run_id], ensure_ascii=False, separators=(",", ":"))
                for run_id in sorted(selected_run_ids)
            )
            + "\n",
            encoding="utf-8",
        )
    runs = _load_runs(snapshot_path)
    if set(runs) != selected_run_ids:
        raise ValueError("Snapshot run final tidak identik dengan selection dua mode.")
    return runs


def _artifact(project_root: Path, relative_path: str) -> dict[str, Any]:
    path = project_root / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Artefak final tidak ditemukan: {relative_path}")
    return {
        "path": relative_path,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def finalize(project_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    captures_root = project_root / "results/captures"
    manifest_path = captures_root / "dataset_manifest_v2.json"
    manifest = _read_json(manifest_path)
    input_validation = validate_manifest(captures_root, manifest)
    expected_capture_ids = {str(row["capture_id"]) for row in manifest["captures"]}

    selections: dict[str, dict[str, Any]] = {}
    selected_run_ids: set[str] = set()
    for mode in ("gemma_only", "sensor_assisted"):
        path = captures_root / f"fresh_run_selection_{mode}_v2.json"
        selection = _read_json(path)
        rows = selection.get("runs") or []
        capture_ids = {str(row["capture_id"]) for row in rows}
        run_ids = {str(row["analysis_run_id"]) for row in rows}
        if (
            selection.get("mode") != mode
            or selection.get("completed") != 18
            or selection.get("failed") != 0
            or len(rows) != 18
            or capture_ids != expected_capture_ids
            or len(run_ids) != 18
        ):
            raise ValueError(f"Run selection final tidak valid: {mode}")
        if selected_run_ids & run_ids:
            raise ValueError("Run ID dipakai lintas mode.")
        selected_run_ids.update(run_ids)
        selections[mode] = selection

    selected_runs_path = captures_root / "dataset_selected_analysis_runs_v2_fresh.jsonl"
    runs = _load_or_freeze_selected_runs(
        selected_runs_path,
        project_root / "results/analysis_runs.jsonl",
        selected_run_ids,
    )
    raw_response_count = 0
    prompt_checksum_count = 0
    display_note_mismatch_count = 0
    run_entries: list[dict[str, Any]] = []
    for mode, selection in selections.items():
        for selection_row in selection["runs"]:
            run_id = str(selection_row["analysis_run_id"])
            capture_id = str(selection_row["capture_id"])
            run = runs.get(run_id)
            if run is None or run.get("capture_id") != capture_id:
                raise ValueError(f"Run/capture mismatch: {run_id}")
            output = (run.get("outputs") or {}).get(mode) or {}
            provenance = output.get("gemma_provenance") or {}
            prompt = str(provenance.get("prompt") or "")
            prompt_sha256 = str(provenance.get("prompt_sha256") or "")
            if output.get("success") is not True or output.get("mode") != mode:
                raise ValueError(f"Output mode tidak valid: {run_id}")
            if _sha256_bytes(prompt.encode("utf-8")) != prompt_sha256:
                raise ValueError(f"Checksum prompt tidak valid: {run_id}")
            prompt_checksum_count += 1
            if provenance.get("raw_response"):
                raw_response_count += 1
            contribution = output.get("sensor_contribution")
            if mode == "gemma_only":
                if contribution is not None or prompt.startswith("Konteks sensor terverifikasi:"):
                    raise ValueError(f"Baseline bocor konteks sensor: {run_id}")
                system_note = str((output.get("display") or {}).get("system_note") or "")
                if "menerima konteks jarak frontal sensor" in system_note:
                    display_note_mismatch_count += 1
            else:
                if (
                    not prompt.startswith("Konteks sensor terverifikasi:")
                    or (contribution or {}).get("status") != "applied"
                ):
                    raise ValueError(f"Sensor conditioning tidak valid: {run_id}")
            run_entries.append(
                {
                    "capture_id": capture_id,
                    "mode": mode,
                    "analysis_run_id": run_id,
                    "prompt_sha256": prompt_sha256,
                    "run_sha256": _canonical_sha256(run),
                    "output_sha256": _canonical_sha256(output),
                    "raw_provider_response_preserved": bool(provenance.get("raw_response")),
                }
            )

    visual_path = captures_root / "dataset_visual_evaluation_v2_fresh.csv"
    key_path = captures_root / "dataset_visual_evaluation_key_v2_fresh.csv"
    score_lock_path = captures_root / "dataset_visual_evaluation_score_lock_v2_fresh.json"
    visual_rows = _read_csv(visual_path)
    key_rows = _read_csv(key_path)
    score_lock = _read_json(score_lock_path)
    visual_ids = {row["evaluation_item_id"] for row in visual_rows}
    key_ids = {row["evaluation_item_id"] for row in key_rows}
    if (
        len(visual_rows) != 36
        or len(key_rows) != 36
        or visual_ids != key_ids
        or any(row.get("manual_review_status") != "completed" for row in visual_rows)
        or _sha256(visual_path) != score_lock.get("scored_template_sha256")
        or score_lock.get("key_opened_during_scoring") is not False
    ):
        raise ValueError("Score lock atau pasangan visual/key tidak valid.")

    blind_manifest = _read_json(
        captures_root / "dataset_visual_evaluation_blind_images_v2_fresh.json"
    )
    blind_hash_counts: Counter[str] = Counter()
    for entry in blind_manifest.get("images") or []:
        path = captures_root / str(entry["blind_image_path"])
        if (
            not path.is_file()
            or path.stat().st_size != entry["size_bytes"]
            or _sha256(path) != entry["sha256"]
        ):
            raise ValueError(f"Gambar blind tidak valid: {path}")
        blind_hash_counts[str(entry["sha256"])] += 1
    if (
        blind_manifest.get("item_count") != 36
        or len(blind_hash_counts) != 18
        or set(blind_hash_counts.values()) != {2}
    ):
        raise ValueError("Struktur 18 citra × 2 mode pada gambar blind tidak valid.")

    visual_summary = _read_json(captures_root / "dataset_visual_summary_v2_fresh.json")
    if (
        visual_summary.get("independent_images") != 18
        or visual_summary.get("scored_items") != 36
        or visual_summary.get("items_per_image") != 2
        or visual_summary.get("scored_template_sha256") != _sha256(visual_path)
    ):
        raise ValueError("Ringkasan visual final tidak valid.")

    artifacts = [_artifact(project_root, path) for path in PRIMARY_ARTIFACTS]
    for path in sorted(
        (captures_root / "visual_review_contact_sheets_v2").glob("*.jpg")
    ):
        artifacts.append(_artifact(project_root, path.relative_to(project_root).as_posix()))

    evaluation_manifest = {
        "schema_version": 2,
        "evaluation_id": "dataset-v2-reanalysis-blind-scored-20260723",
        "dataset_id": manifest["dataset_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_manifest_sha256": _sha256(manifest_path),
        "input_validation": input_validation,
        "analysis_runs": {
            "path": "results/captures/dataset_selected_analysis_runs_v2_fresh.jsonl",
            "whole_log_checksum_included": True,
            "whole_log_sha256": _sha256(selected_runs_path),
            "selected_run_count": len(run_entries),
            "unique_selected_run_ids": len(selected_run_ids),
            "raw_provider_response_preserved_count": raw_response_count,
            "prompt_checksum_verified_count": prompt_checksum_count,
        },
        "selected_runs": run_entries,
        "visual_evaluation": {
            "design": "paired_blind_single_evaluator",
            "independent_images": 18,
            "scored_items": 36,
            "items_per_image": 2,
            "blind_image_unique_checksums": len(blind_hash_counts),
            "each_source_image_copy_count": 2,
            "score_lock_sha256": _sha256(score_lock_path),
            "key_opened_during_scoring": False,
        },
        "bias_controls": [
            "hasil lama dikeluarkan sebelum paket final dibekukan",
            "mode, jarak, capture ID, run ID, model, dan prompt disembunyikan dari template",
            "nama gambar evaluator dinetralkan menjadi VE-*",
            "skor dikunci checksum sebelum key dibuka",
            "analisis statistik memakai 18 pasangan capture",
            "bootstrap meresampling pasangan capture",
        ],
        "known_issues": [
            {
                "issue": "baseline display.system_note menyatakan konteks sensor meski prompt baseline default",
                "affected_selected_runs": display_note_mismatch_count,
                "impact": "note pascainferensi tidak masuk prompt atau template blind; implementasi diperbaiki setelah audit",
            }
        ],
        "artifacts": artifacts,
        "claim_boundaries": [
            "bukan UAT",
            "bukan bukti keselamatan navigasi atau manfaat pengguna",
            "referensi sensor frontal bukan jarak ke objek yang dinamai Gemma",
            "satu objek dan satu setup tidak mendukung generalisasi multiobjek",
            "satu evaluator tidak menyediakan inter-rater agreement",
        ],
    }
    evaluation_path = captures_root / "evaluation_manifest_v2_fresh.json"
    evaluation_path.write_text(
        json.dumps(evaluation_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    artifact_checks = sum(
        (
            project_root / artifact["path"]
        ).is_file()
        and (project_root / artifact["path"]).stat().st_size == artifact["size_bytes"]
        and _sha256(project_root / artifact["path"]) == artifact["sha256"]
        for artifact in artifacts
    )
    validation = {
        "valid": artifact_checks == len(artifacts),
        "evaluation_id": evaluation_manifest["evaluation_id"],
        "dataset_id": manifest["dataset_id"],
        "input_captures_verified": input_validation["checksums_verified"],
        "selected_runs_verified": len(run_entries),
        "unique_selected_run_ids": len(selected_run_ids),
        "raw_provider_responses_preserved": raw_response_count,
        "prompt_checksums_verified": prompt_checksum_count,
        "visual_items_scored": len(visual_rows),
        "independent_images": len(blind_hash_counts),
        "paired_mode_copies_per_image": 2,
        "score_lock_verified": True,
        "artifact_checksums_verified": artifact_checks,
        "artifact_count": len(artifacts),
        "known_display_note_mismatches": display_note_mismatch_count,
    }
    if not validation["valid"]:
        raise ValueError("Checksum artefak final tidak valid.")
    validation_path = captures_root / "evaluation_manifest_v2_fresh_validation.json"
    validation_path.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return evaluation_manifest, validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Kunci dan validasi paket evaluasi final dataset v2.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    _, validation = finalize(args.project_root.resolve())
    print(json.dumps(validation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
