import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def build_contact_sheets(
    image_dir: Path,
    output_dir: Path,
    *,
    columns: int = 3,
    rows: int = 2,
) -> list[Path]:
    image_paths = sorted(image_dir.glob("VE-*.jpg"))
    if not image_paths:
        raise ValueError(f"Gambar blind tidak ditemukan: {image_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=24)
    sample = Image.open(image_paths[0])
    cell_width = sample.width
    cell_height = sample.height + 40
    per_sheet = columns * rows
    outputs: list[Path] = []
    for sheet_index, start in enumerate(range(0, len(image_paths), per_sheet), 1):
        sheet_paths = image_paths[start : start + per_sheet]
        sheet = Image.new(
            "RGB",
            (columns * cell_width, rows * cell_height),
            "white",
        )
        draw = ImageDraw.Draw(sheet)
        for index, image_path in enumerate(sheet_paths):
            image = Image.open(image_path).convert("RGB")
            column = index % columns
            row = index // columns
            x = column * cell_width
            y = row * cell_height
            sheet.paste(image, (x, y + 40))
            draw.text((x + 8, y + 7), image_path.stem, fill="black", font=font)
        output_path = output_dir / f"blind_review_sheet_{sheet_index:02d}.jpg"
        sheet.save(output_path, quality=95)
        outputs.append(output_path)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Bangun contact sheet gambar evaluasi blind.")
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("results/captures/images/visual_evaluation_blind_v2"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/captures/visual_review_contact_sheets_v2"),
    )
    args = parser.parse_args()
    outputs = build_contact_sheets(args.image_dir, args.output_dir)
    print("\n".join(path.as_posix() for path in outputs))


if __name__ == "__main__":
    main()
