import json

import pytest

from scripts.finalize_dataset_v2_evaluation import _load_or_freeze_selected_runs


def _run(run_id: str) -> dict:
    return {"schema_version": 1, "analysis_run_id": run_id}


def test_selected_run_snapshot_is_frozen_from_runtime_log(tmp_path) -> None:
    runtime_log = tmp_path / "analysis_runs.jsonl"
    runtime_log.write_text(
        "\n".join(json.dumps(_run(run_id)) for run_id in ("run-b", "old-run", "run-a"))
        + "\n",
        encoding="utf-8",
    )
    snapshot = tmp_path / "selected.jsonl"

    runs = _load_or_freeze_selected_runs(
        snapshot,
        runtime_log,
        {"run-a", "run-b"},
    )

    assert set(runs) == {"run-a", "run-b"}
    assert "old-run" not in snapshot.read_text(encoding="utf-8")


def test_existing_snapshot_must_match_selected_run_ids(tmp_path) -> None:
    snapshot = tmp_path / "selected.jsonl"
    snapshot.write_text(json.dumps(_run("wrong-run")) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="tidak identik"):
        _load_or_freeze_selected_runs(
            snapshot,
            tmp_path / "unused-runtime-log.jsonl",
            {"run-a"},
        )
