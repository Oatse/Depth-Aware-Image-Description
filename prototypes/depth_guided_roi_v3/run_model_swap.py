#!/usr/bin/env -S python

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

import anyio
import typer


PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from prototypes.depth_guided_roi_v3.strong_model_diagnostic import run_diagnostic, write_diagnostic


DEFAULT_SOURCE_ROOT: Final = (
    PROJECT_ROOT / "results" / "prototypes" / "depth_guided_roi_v3_final_run_20260715"
)
DEFAULT_OUTPUT_ROOT: Final = (
    PROJECT_ROOT / "results" / "prototypes" / "depth_guided_roi_v3_modelswap_cx_gpt55_20260715"
)


async def _run(source_root: Path, output_root: Path, model: str, base_url: str) -> None:
    settings = get_settings().model_copy(
        update={
            "lm_studio_url": base_url.removesuffix("/v1"),
            "lm_studio_model": model,
            "lm_studio_timeout": 240,
        }
    )
    bundle = await run_diagnostic(settings, source_root, output_root)
    write_diagnostic(output_root, bundle, model)


def main(
    source_root: Path = typer.Option(DEFAULT_SOURCE_ROOT, exists=True, file_okay=False),
    output_root: Path = typer.Option(DEFAULT_OUTPUT_ROOT, file_okay=False),
    model: str = typer.Option("cx/gpt-5.5"),
    base_url: str = typer.Option("http://127.0.0.1:20128/v1"),
) -> None:
    anyio.run(_run, source_root, output_root, model, base_url)


if __name__ == "__main__":
    typer.run(main)
