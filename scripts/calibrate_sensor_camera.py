import argparse
import json
from pathlib import Path

from services.sensor_calibration import validate_calibration_measurements


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("measurements", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    measurements = json.loads(args.measurements.read_text(encoding="utf-8"))
    result = validate_calibration_measurements(measurements)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if result["validated"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
