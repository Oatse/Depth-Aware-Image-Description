from __future__ import annotations

import base64
import json
from pathlib import Path

import requests


root = Path(__file__).resolve().parents[2]
image_path = root / "results" / "prototypes" / "confidence_gated_spatial_calibration_holdout_20260718" / "samples" / "holdout_015_rgb.jpg"
encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
payload = {
    "model": "google/gemma-4-e2b",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Balas JSON singkat dengan field description."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
            ],
        }
    ],
    "temperature": 0.1,
    "max_tokens": 64,
}
response = requests.post(
    "http://localhost:1234/v1/chat/completions",
    json=payload,
    timeout=60,
)
print(json.dumps({"status_code": response.status_code, "body": response.text[:4000]}, ensure_ascii=False, indent=2))

