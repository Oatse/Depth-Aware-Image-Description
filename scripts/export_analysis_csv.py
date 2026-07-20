import argparse
import csv
from pathlib import Path

from services.run_repository import RunRepository


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = []
    for record in RunRepository(args.source).read_all():
        for mode, output in sorted((record.get("outputs") or {}).items()):
            rows.append(
                {
                    "analysis_run_id": record["analysis_run_id"],
                    "capture_id": record.get("capture_id") or "",
                    "mode": mode,
                    "success": output.get("success", ""),
                    "final_description": output.get("final_description", ""),
                    "error": output.get("error", ""),
                }
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["analysis_run_id", "capture_id", "mode", "success", "final_description", "error"])
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
