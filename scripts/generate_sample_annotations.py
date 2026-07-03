import argparse
import csv
from pathlib import Path


FIELDS = [
    "image_name",
    "main_object",
    "object_position",
    "distance_meter",
    "distance_category",
    "has_obstacle",
    "front_area_status",
    "safer_direction",
    "notes",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate annotation template rows from dataset images.")
    parser.add_argument("--images-dir", type=Path, default=Path("dataset/images"))
    parser.add_argument("--output", type=Path, default=Path("dataset/annotations.csv"))
    args = parser.parse_args()

    image_paths = sorted(
        path for path in args.images_dir.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for image_path in image_paths:
            writer.writerow({"image_name": image_path.name})

    print(f"Wrote {len(image_paths)} annotation rows to {args.output}")


if __name__ == "__main__":
    main()
