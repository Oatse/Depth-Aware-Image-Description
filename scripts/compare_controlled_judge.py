from __future__ import annotations

import argparse
import csv
import random
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from statistics import fmean


DEFAULT_METRICS = (
    "semantic_correctness_mean",
    "spatial_accuracy_mean",
    "groundedness_mean",
    "clarity_mean",
    "overall_mean",
)


def compare_judge_rows(
    legacy_rows: Iterable[Mapping[str, str]],
    constrained_rows: Iterable[Mapping[str, str]],
    *,
    metrics: Sequence[str] = DEFAULT_METRICS,
    bootstrap_samples: int = 10_000,
    seed: int = 20260714,
) -> list[dict[str, str | int | float]]:
    if bootstrap_samples < 1:
        raise ValueError("bootstrap_samples must be positive")

    legacy = _index_unique_rows(legacy_rows, label="legacy")
    constrained = _index_unique_rows(constrained_rows, label="constrained")
    if legacy.keys() != constrained.keys():
        missing_constrained = sorted(legacy.keys() - constrained.keys())
        missing_legacy = sorted(constrained.keys() - legacy.keys())
        raise ValueError(
            "paired image sets differ: "
            f"missing_constrained={missing_constrained}, missing_legacy={missing_legacy}"
        )
    if not legacy:
        raise ValueError("judge inputs contain no rows")

    ordered_images = sorted(legacy)
    output: list[dict[str, str | int | float]] = []
    for metric_index, metric in enumerate(metrics):
        legacy_values = [_score(legacy[name], metric) for name in ordered_images]
        constrained_values = [_score(constrained[name], metric) for name in ordered_images]
        differences = [
            constrained_value - legacy_value
            for legacy_value, constrained_value in zip(
                legacy_values, constrained_values, strict=True
            )
        ]
        lower, upper = _paired_bootstrap_interval(
            differences,
            samples=bootstrap_samples,
            seed=seed + metric_index,
        )
        mean_difference = fmean(differences)
        output.append(
            {
                "metric": metric,
                "paired_images": len(ordered_images),
                "legacy_mean": fmean(legacy_values),
                "constrained_mean": fmean(constrained_values),
                "mean_difference": mean_difference,
                "bootstrap_95_low": lower,
                "bootstrap_95_high": upper,
                "wins": sum(value > 0 for value in differences),
                "ties": sum(value == 0 for value in differences),
                "losses": sum(value < 0 for value in differences),
                "snapshot_direction": _direction(mean_difference),
                "interval_excludes_zero": "yes" if lower > 0 or upper < 0 else "no",
            }
        )
    return output


def _index_unique_rows(
    rows: Iterable[Mapping[str, str]], *, label: str
) -> dict[str, Mapping[str, str]]:
    indexed: dict[str, Mapping[str, str]] = {}
    for row in rows:
        image_name = row.get("image_name", "").strip()
        if not image_name:
            raise ValueError(f"{label} judge row is missing image_name")
        if image_name in indexed:
            raise ValueError(f"duplicate {label} judge row for {image_name}")
        indexed[image_name] = row
    return indexed


def _score(row: Mapping[str, str], metric: str) -> float:
    value = row.get(metric, "").strip()
    if not value:
        raise ValueError(f"judge row is missing metric {metric}")
    return float(value)


def _paired_bootstrap_interval(
    differences: Sequence[float], *, samples: int, seed: int
) -> tuple[float, float]:
    generator = random.Random(seed)
    size = len(differences)
    means = sorted(
        fmean(differences[generator.randrange(size)] for _ in range(size))
        for _ in range(samples)
    )
    return _percentile(means, 0.025), _percentile(means, 0.975)


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index
    return (
        sorted_values[lower_index] * (1 - fraction)
        + sorted_values[upper_index] * fraction
    )


def _direction(mean_difference: float) -> str:
    if mean_difference > 0:
        return "constrained_higher"
    if mean_difference < 0:
        return "legacy_higher"
    return "equal"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two image-aware judge files using paired image rows."
    )
    parser.add_argument("--legacy", type=Path, required=True)
    parser.add_argument("--constrained", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260714)
    args = parser.parse_args()

    rows = compare_judge_rows(
        _read_csv(args.legacy),
        _read_csv(args.constrained),
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    _write_csv(args.output, rows)
    print(f"Wrote {len(rows)} paired metric rows to {args.output}")


if __name__ == "__main__":
    main()
