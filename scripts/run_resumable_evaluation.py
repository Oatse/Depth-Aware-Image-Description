import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_batch_evaluation import DEFAULT_MODES, _read_successful_job_keys
from services.experiment_preflight import IMAGE_EXTENSIONS

DEFAULT_LIMIT_JOBS: Final[int] = 2


@dataclass(frozen=True, slots=True)
class ResumableRunConfig:
    images_dir: Path
    annotations_path: Path
    predictions_path: Path
    evaluation_path: Path
    modes: tuple[str, ...]
    limit_jobs: int
    max_runs: int | None = None
    allow_mock: bool = False


def _expected_job_keys(config: ResumableRunConfig) -> set[tuple[str, str]]:
    image_names = sorted(
        path.name
        for path in config.images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    return {
        (image_name, mode)
        for image_name in image_names
        for mode in config.modes
    }


def _completed_job_count(config: ResumableRunConfig) -> int:
    expected_jobs = _expected_job_keys(config)
    completed_jobs = _read_successful_job_keys(config.predictions_path)
    return len(expected_jobs & completed_jobs)


def _build_partial_command(config: ResumableRunConfig) -> list[str]:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "run_batch_evaluation.py"),
        "--images-dir",
        str(config.images_dir),
        "--annotations",
        str(config.annotations_path),
        "--predictions",
        str(config.predictions_path),
        "--output",
        str(config.evaluation_path),
        "--resume",
        "--limit-jobs",
        str(config.limit_jobs),
        "--modes",
        *config.modes,
    ]
    if config.allow_mock:
        command.append("--allow-mock")
    return command


def run_resumable_evaluation(config: ResumableRunConfig) -> int:
    expected_jobs = _expected_job_keys(config)
    if not expected_jobs:
        print(f"No image-mode jobs found in {config.images_dir}.", flush=True)
        return 1

    run_count = 0
    while True:
        completed_before = _completed_job_count(config)
        remaining_before = len(expected_jobs) - completed_before
        if remaining_before == 0:
            print("All evaluation jobs are already complete.", flush=True)
            return 0
        if config.max_runs is not None and run_count >= config.max_runs:
            print(f"Stopped after {run_count} runs. Remaining jobs: {remaining_before}.", flush=True)
            return 0

        run_count += 1
        print(f"Run {run_count}: {remaining_before} jobs remaining.", flush=True)
        result = subprocess.run(_build_partial_command(config), cwd=PROJECT_ROOT, check=False)
        if result.returncode != 0:
            print(f"Stopped because partial run failed with exit code {result.returncode}.", flush=True)
            return result.returncode

        completed_after = _completed_job_count(config)
        if completed_after <= completed_before:
            print("Stopped because the last partial run did not complete any new successful job.", flush=True)
            return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run resumable evaluation jobs sequentially.")
    parser.add_argument("--images-dir", type=Path, default=Path("dataset/images"))
    parser.add_argument("--annotations", type=Path, default=Path("dataset/annotations.csv"))
    parser.add_argument("--predictions", type=Path, default=Path("results/predictions.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/evaluation.csv"))
    parser.add_argument("--modes", nargs="+", default=list(DEFAULT_MODES))
    parser.add_argument("--limit-jobs", type=int, default=DEFAULT_LIMIT_JOBS)
    parser.add_argument("--max-runs", type=int)
    parser.add_argument("--allow-mock", action="store_true")
    args = parser.parse_args()

    if args.limit_jobs < 1:
        parser.error("--limit-jobs must be greater than 0.")
    if args.max_runs is not None and args.max_runs < 1:
        parser.error("--max-runs must be greater than 0.")

    raise SystemExit(
        run_resumable_evaluation(
            ResumableRunConfig(
                images_dir=args.images_dir,
                annotations_path=args.annotations,
                predictions_path=args.predictions,
                evaluation_path=args.output,
                modes=tuple(args.modes),
                limit_jobs=args.limit_jobs,
                max_runs=args.max_runs,
                allow_mock=args.allow_mock,
            )
        )
    )


if __name__ == "__main__":
    main()
