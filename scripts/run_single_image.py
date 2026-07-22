import argparse
import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from services.analysis_types import AnalysisMode
from services.pipeline import analyze_image_bytes


async def run_single_image(image_path: Path, mode: AnalysisMode) -> dict:
    settings = get_settings()
    result = await analyze_image_bytes(
        image_path.read_bytes(),
        image_path.name,
        mode,
        settings,
    )
    return {
        "success": result.success,
        "mode": result.mode.value,
        "gemma_description": result.gemma_description,
        "final_description": result.final_description,
        "sensor_contribution": result.sensor_contribution,
        "latency": result.latency,
        "error": result.error,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one RGB image through the active analysis pipeline.")
    parser.add_argument("image_path", type=Path)
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in AnalysisMode],
        default=AnalysisMode.SENSOR_ASSISTED.value,
    )
    args = parser.parse_args()
    result = asyncio.run(run_single_image(args.image_path, AnalysisMode(args.mode)))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
