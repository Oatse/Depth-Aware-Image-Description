import argparse
import csv
import os
import sys
from dataclasses import asdict
from pathlib import Path

import anyio


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.llm_judge import JUDGE_RUBRIC_VERSION, OpenAIImageJudge
from services.image_preprocess import preprocess_image


async def run_judge(
    annotations_path: Path,
    predictions_path: Path,
    images_dir: Path,
    output_path: Path,
    cache_dir: Path,
    api_key: str,
    model: str,
    base_url: str,
    repeats: int,
    modes: set[str] | None,
    limit: int | None,
) -> None:
    annotations = _read_csv(annotations_path)
    annotation_by_name = {row.get("image_name", ""): row for row in annotations}
    predictions = [
        row
        for row in _read_csv(predictions_path)
        if not row.get("error")
        and row.get("final_description", "").strip()
        and (modes is None or row.get("mode", "") in modes)
        and row.get("image_name", "") in annotation_by_name
    ]
    selected = predictions[:limit] if limit is not None else predictions
    missing_images = [
        prediction["image_name"]
        for prediction in selected
        if not (images_dir / prediction["image_name"]).is_file()
    ]
    if missing_images:
        raise FileNotFoundError(
            f"Missing judge images in {images_dir}: {', '.join(sorted(missing_images))}"
        )
    judge = OpenAIImageJudge(
        api_key=api_key,
        cache_dir=cache_dir,
        model=model,
        base_url=base_url,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "image_name",
        "mode",
        "judge_model",
        "rubric_version",
        "repeat_count",
        "semantic_correctness_mean",
        "spatial_accuracy_mean",
        "groundedness_mean",
        "clarity_mean",
        "overall_mean",
        "overall_stddev",
        "visual_evidence_union",
        "critical_error_union",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, prediction in enumerate(selected, start=1):
            aggregate = await judge.judge(
                annotation_by_name[prediction["image_name"]],
                prediction,
                _image_data_url(images_dir / prediction["image_name"]),
                repeats=repeats,
            )
            row = asdict(aggregate)
            row["visual_evidence_union"] = " | ".join(aggregate.visual_evidence_union)
            row["critical_error_union"] = " | ".join(aggregate.critical_error_union)
            writer.writerow({
                "image_name": prediction["image_name"],
                "mode": prediction.get("mode", "all") or "all",
                "judge_model": judge.model,
                "rubric_version": JUDGE_RUBRIC_VERSION,
                **row,
            })
            handle.flush()
            print(f"{index}/{len(selected)} | {prediction['image_name']} | {prediction.get('mode', 'all')}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _image_data_url(path: Path) -> str:
    processed = preprocess_image(path.read_bytes(), max_dimension=768)
    return f"data:image/jpeg;base64,{processed.base64_image}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a blinded, repeated image-aware LLM judge.")
    parser.add_argument("--annotations", type=Path, default=Path("dataset/final_annotations.csv"))
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--images-dir", type=Path, default=Path("dataset/final_images"))
    parser.add_argument("--output", type=Path, default=Path("results/llm_judge.csv"))
    parser.add_argument("--cache-dir", type=Path, default=Path("results/llm_judge_cache"))
    parser.add_argument("--model", default="gpt-4o-mini-2024-07-18")
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--modes", nargs="+")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be greater than 0")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than 0")
    api_key = os.getenv(args.api_key_env, "")
    if not api_key:
        parser.error(
            f"Environment variable {args.api_key_env} is required. No external judge request was sent."
        )
    anyio.run(
        run_judge,
        args.annotations,
        args.predictions,
        args.images_dir,
        args.output,
        args.cache_dir,
        api_key,
        args.model,
        args.base_url,
        args.repeats,
        set(args.modes) if args.modes else None,
        args.limit,
    )


if __name__ == "__main__":
    main()
