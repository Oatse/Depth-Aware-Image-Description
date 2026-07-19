from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from app.config import Settings
from models.gemma_client import GemmaClient, GemmaClientError
from services.image_preprocess import preprocess_image


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "results" / "prototypes" / "confidence_gated_spatial_calibration_holdout_20260718"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="google/gemma-4-e2b")
    parser.add_argument("--sample-index", type=int, default=15)
    parser.add_argument("--timeout", type=float, default=90.0)
    return parser.parse_args()


async def run_probe(model: str, sample_index: int, timeout: float) -> dict:
    image_path = SOURCE_DIR / "samples" / f"holdout_{sample_index:03d}_rgb.jpg"
    settings = Settings(lm_studio_model=model, lm_studio_timeout=int(timeout))
    client = GemmaClient(settings)
    started = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            client.describe_image(
                preprocess_image(image_path.read_bytes(), 768).base64_image,
            ),
            timeout=timeout,
        )
        return {
            "model": model,
            "sample_index": sample_index,
            "status": "success",
            "latency_ms": result.latency_ms,
            "structured": result.structured is not None,
            "description_length": len(result.description),
            "wall_seconds": round(time.perf_counter() - started, 6),
            "error": "",
        }
    except (asyncio.TimeoutError, GemmaClientError, OSError, ValueError) as exc:
        return {
            "model": model,
            "sample_index": sample_index,
            "status": "timeout_or_error",
            "latency_ms": 0,
            "structured": False,
            "description_length": 0,
            "wall_seconds": round(time.perf_counter() - started, 6),
            "error": str(exc),
        }


def main() -> int:
    args = parse_args()
    result = asyncio.run(run_probe(args.model, args.sample_index, args.timeout))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())

