import argparse
import json
from pathlib import Path

from services.evaluator import evaluate_iot_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = evaluate_iot_manifest(args.manifest)
    payload = {name: getattr(summary, name) for name in summary.__dataclass_fields__}
    text = json.dumps(payload, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
