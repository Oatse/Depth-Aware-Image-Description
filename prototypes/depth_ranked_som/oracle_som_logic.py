from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Final, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from prototypes.depth_ranked_som.prototype_models import (
    CLASS_NAMES,
    CLASS_TERMS,
    MARK_COLORS,
    AnnotationFormatError,
    DepthShapeError,
    PrototypeSample,
    RankedMark,
    YoloBox,
)


def parse_yolo_labels(path: Path) -> tuple[YoloBox, ...]:
    boxes: list[YoloBox] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        content = raw_line.strip()
        if not content:
            continue
        parts = content.split()
        if len(parts) != 5:
            raise AnnotationFormatError(path, line_number, content)
        try:
            class_id, center_x, center_y, width, height = (float(part) for part in parts)
        except ValueError as exc:
            raise AnnotationFormatError(path, line_number, content) from exc
        if not class_id.is_integer():
            raise AnnotationFormatError(path, line_number, content)
        boxes.append(
            YoloBox(
                class_id=int(class_id),
                center_x=center_x,
                center_y=center_y,
                width=width,
                height=height,
            )
        )
    return tuple(boxes)


def select_validation_samples(dataset_root: Path, limit: int) -> tuple[PrototypeSample, ...]:
    image_dir = dataset_root / "images" / "val"
    label_dir = dataset_root / "labels" / "val"
    candidates: list[PrototypeSample] = []
    for image_path in sorted(image_dir.iterdir(), key=lambda item: item.name.casefold()):
        if image_path.suffix.casefold() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        label_path = label_dir / f"{image_path.stem}.txt"
        if not label_path.exists():
            continue
        boxes = parse_yolo_labels(label_path)
        if len(boxes) >= 2:
            candidates.append(PrototypeSample(image_path, label_path, boxes))

    selected: list[PrototypeSample] = []
    uncovered = set(range(len(CLASS_NAMES)))
    remaining = candidates.copy()
    while remaining and len(selected) < limit:
        remaining.sort(
            key=lambda sample: (
                -len({box.class_id for box in sample.boxes} & uncovered),
                sample.image_path.name.casefold(),
            )
        )
        chosen = remaining.pop(0)
        selected.append(chosen)
        uncovered.difference_update(box.class_id for box in chosen.boxes)
    return tuple(selected)


def rank_boxes_by_depth(
    depth_map: np.ndarray,
    boxes: Sequence[YoloBox],
    limit: int = 3,
) -> tuple[RankedMark, ...]:
    if depth_map.ndim != 2:
        raise DepthShapeError(depth_map.shape)
    height, width = depth_map.shape
    scored: list[tuple[float, float, YoloBox]] = []
    for box in boxes:
        left, top, right, bottom = box.bounds()
        inset_x = (right - left) * 0.1
        inset_y = (bottom - top) * 0.1
        x1 = max(0, min(width - 1, math.floor((left + inset_x) * width)))
        y1 = max(0, min(height - 1, math.floor((top + inset_y) * height)))
        x2 = max(x1 + 1, min(width, math.ceil((right - inset_x) * width)))
        y2 = max(y1 + 1, min(height, math.ceil((bottom - inset_y) * height)))
        finite = depth_map[y1:y2, x1:x2]
        finite = finite[np.isfinite(finite)]
        if finite.size:
            scored.append((float(np.median(finite)), float(np.percentile(finite, 10)), box))

    scored.sort(key=lambda item: (item[0], item[1], item[2].class_id))
    return tuple(
        RankedMark(mark_id=index, box=box, median_depth=median, p10_depth=p10)
        for index, (median, p10, box) in enumerate(scored[:limit], start=1)
    )


def draw_marks(image: Image.Image, marks: Sequence[RankedMark]) -> Image.Image:
    marked = image.convert("RGB").copy()
    draw = ImageDraw.Draw(marked)
    font_size = max(28, min(64, marked.height // 18))
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except OSError:
        font = ImageFont.load_default(size=font_size)
    for mark in marks:
        color = MARK_COLORS[(mark.mark_id - 1) % len(MARK_COLORS)]
        left, top, right, bottom = mark.box.bounds()
        pixels = (
            round(left * marked.width),
            round(top * marked.height),
            round(right * marked.width),
            round(bottom * marked.height),
        )
        line_width = max(5, marked.width // 140)
        draw.rectangle(pixels, outline=color, width=line_width)
        label = f"MARK {mark.mark_id}"
        label_box = draw.textbbox((0, 0), label, font=font, stroke_width=2)
        label_width = label_box[2] - label_box[0] + 18
        label_height = label_box[3] - label_box[1] + 14
        label_left = max(0, min(pixels[0], marked.width - label_width))
        preferred_top = pixels[1] - label_height
        label_top = max(0, min(preferred_top if preferred_top >= 0 else pixels[1], marked.height - label_height))
        badge = (label_left, label_top, label_left + label_width, label_top + label_height)
        draw.rectangle(badge, fill=color, outline=(0, 0, 0), width=3)
        draw.text(
            (label_left + 9, label_top + 5),
            label,
            fill=(255, 255, 255),
            font=font,
            stroke_width=2,
            stroke_fill=(0, 0, 0),
        )
    return marked


def depth_visual(depth_map: np.ndarray) -> Image.Image:
    finite = np.nan_to_num(depth_map, nan=0.0, posinf=0.0, neginf=0.0)
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    normalized = np.zeros_like(finite) if maximum <= minimum else (finite - minimum) / (maximum - minimum)
    return Image.fromarray((normalized * 255).astype(np.uint8))


def build_mark_prompt(mark_ids: Sequence[int]) -> str:
    ids = ", ".join(str(mark_id) for mark_id in mark_ids)
    return (
        "Amati gambar indoor yang memiliki kotak dan nomor visual. "
        f"Identifikasi hanya objek di dalam kotak berbadge MARK {ids}. "
        "Angka pada badge adalah ID region, bukan nama objek. Jangan menebak objek di luar kotak dan jangan memakai informasi depth. "
        "Balas hanya JSON valid tanpa markdown dengan skema "
        '{"marks":[{"id":1,"object":"nama objek Bahasa Indonesia"}],'
        '"description":"satu kalimat ringkas tentang objek bertanda"}. '
        "Sertakan tepat satu entri untuk setiap badge MARK yang terlihat, jangan membuat ID baru, dan langsung keluarkan JSON tanpa penalaran."
    )


def prediction_matches(class_id: int, prediction: str) -> bool:
    normalized = " ".join(re.sub(r"[^a-z0-9 ]+", " ", prediction.casefold()).split())
    tokens = set(normalized.split())
    for term in CLASS_TERMS[class_id]:
        normalized_term = " ".join(re.sub(r"[^a-z0-9 ]+", " ", term.casefold()).split())
        if " " in normalized_term and normalized_term in normalized:
            return True
        if normalized_term in tokens:
            return True
    return False


def make_contact_sheet(paths: Sequence[Path], output_path: Path, cell_size: int = 360) -> None:
    columns = 3
    rows = math.ceil(len(paths) / columns)
    sheet = Image.new("RGB", (columns * cell_size, rows * cell_size), color=(245, 245, 245))
    for index, path in enumerate(paths):
        with Image.open(path) as opened:
            image = ImageOps.contain(opened.convert("RGB"), (cell_size - 16, cell_size - 36))
        x = (index % columns) * cell_size + (cell_size - image.width) // 2
        y = (index // columns) * cell_size + 28
        sheet.paste(image, (x, y))
        ImageDraw.Draw(sheet).text(((index % columns) * cell_size + 8, (index // columns) * cell_size + 8), path.stem, fill=(0, 0, 0))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=90)
