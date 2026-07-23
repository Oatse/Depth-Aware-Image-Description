import argparse
import json
from pathlib import Path

from scripts.freeze_capture_dataset import validate_manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validasi manifest dataset capture terhadap gambar dan metadata sumber."
    )
    parser.add_argument("--captures-root", type=Path, default=Path("results/captures"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("results/captures/dataset_manifest_v2.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/captures/dataset_manifest_v2_validation.json"),
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = validate_manifest(args.captures_root, manifest)
    result["manifest_path"] = args.manifest.as_posix()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
