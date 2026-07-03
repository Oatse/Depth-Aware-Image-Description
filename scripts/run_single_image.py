import argparse
import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from models.depth_anything import DepthAnything
from models.fusion import fuse_description
from models.gemma_client import GemmaClient, GemmaClientError
from services.depth_analysis import analyze_depth_regions
from services.image_preprocess import preprocess_image


async def run_single_image(image_path: Path, mode: str) -> dict:
    settings = get_settings()
    image_bytes = image_path.read_bytes()
    processed = preprocess_image(image_bytes, settings.image_max_dimension)

    gemma_description = None
    if mode in {"gemma_only", "gemma_depth"}:
        gemma_client = GemmaClient(settings)
        gemma_result = await gemma_client.describe_image(processed.base64_image)
        gemma_description = gemma_result.description

    depth_summary = None
    if mode in {"depth_only", "gemma_depth"}:
        depth_result = DepthAnything(settings).estimate(processed.image, image_path.name)
        if not depth_result.success:
            if mode == "depth_only":
                raise RuntimeError(depth_result.error or "Depth inference failed.")
        else:
            depth_summary = analyze_depth_regions(depth_result.depth_map)

    return fuse_description(gemma_description, depth_summary, mode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one image through the analysis pipeline.")
    parser.add_argument("image_path", type=Path)
    parser.add_argument("--mode", choices=["gemma_only", "depth_only", "gemma_depth"], default="gemma_depth")
    args = parser.parse_args()

    try:
        result = asyncio.run(run_single_image(args.image_path, args.mode))
    except GemmaClientError as exc:
        raise SystemExit(str(exc)) from exc

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
