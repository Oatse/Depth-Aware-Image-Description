from pathlib import Path

from scripts.run_resumable_evaluation import ResumableRunConfig, _build_partial_command


def test_build_partial_command_runs_batch_with_resume_and_limit(tmp_path: Path) -> None:
    config = ResumableRunConfig(
        images_dir=tmp_path / "images",
        annotations_path=tmp_path / "annotations.csv",
        predictions_path=tmp_path / "predictions.csv",
        evaluation_path=tmp_path / "evaluation.csv",
        modes=("gemma_only", "gemma_depth"),
        limit_jobs=2,
    )

    command = _build_partial_command(config)

    assert "run_batch_evaluation.py" in command[1]
    assert "--resume" in command
    assert command[command.index("--limit-jobs") + 1] == "2"
    assert command[-2:] == ["gemma_only", "gemma_depth"]
