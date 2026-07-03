import argparse
import io
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the running backend or start one temporarily.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--start-server", action="store_true")
    args = parser.parse_args()

    process = None
    if args.start_server:
        env = {
            **os.environ,
            "GEMMA_MOCK": "true",
            "DEPTH_MOCK": "true",
        }
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)

    try:
        health = requests.get(f"{args.base_url}/health", timeout=10)
        health.raise_for_status()
        image_bytes = _sample_image_bytes()
        analyze = requests.post(
            f"{args.base_url}/analyze",
            files={"image": ("sample.jpg", image_bytes, "image/jpeg")},
            data={"mode": "gemma_depth", "save_result": "false"},
            timeout=30,
        )
        analyze.raise_for_status()
        data = analyze.json()
        required_fields = {"success", "final_description", "latency", "mode"}
        missing = required_fields - set(data.keys())
        if missing:
            raise RuntimeError(f"Missing fields: {', '.join(sorted(missing))}")
        if not data["success"]:
            raise RuntimeError(data.get("error") or "Analyze response was not successful.")
        print("Smoke test passed.")
    finally:
        if process is not None:
            process.terminate()
            process.wait(timeout=10)


def _sample_image_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (96, 64), color=(180, 190, 170)).save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


if __name__ == "__main__":
    main()
