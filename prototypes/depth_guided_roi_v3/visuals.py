from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence

from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np

from prototypes.depth_guided_roi_v3.models import CLASS_NAMES, RegionMark, YoloBox


MARK_COLORS: Final = ((239, 68, 68), (245, 158, 11), (6, 182, 212))


@dataclass(frozen=True, slots=True)
class BadgeRequest:
    mark_id: int
    box_pixels: tuple[int, int, int, int]
    badge_size: tuple[int, int]
    canvas_size: tuple[int, int]


def _badge_rectangle(
    request: BadgeRequest,
    occupied: Sequence[tuple[int, int, int, int]],
) -> tuple[int, int, int, int]:
    left, top, right, bottom = request.box_pixels
    badge_width, badge_height = request.badge_size
    canvas_width, canvas_height = request.canvas_size
    candidates = (
        (left + 4, top + 4),
        (left + 4, bottom - badge_height - 4),
        (right - badge_width - 4, top + 4),
        (left, top - badge_height - 4),
        (left, bottom + 4),
    )
    rotation = (request.mark_id - 1) % 3
    ordered = candidates[rotation:3] + candidates[:rotation] + candidates[3:]
    clamped = tuple(
        (
            max(0, min(x, canvas_width - badge_width)),
            max(0, min(y, canvas_height - badge_height)),
        )
        for x, y in ordered
    )
    rectangles = tuple((x, y, x + badge_width, y + badge_height) for x, y in clamped)
    for rectangle in rectangles:
        if all(
            rectangle[2] <= used[0]
            or rectangle[0] >= used[2]
            or rectangle[3] <= used[1]
            or rectangle[1] >= used[3]
            for used in occupied
        ):
            return rectangle
    return rectangles[0]


def depth_visual(depth_map: np.ndarray) -> Image.Image:
    finite = np.nan_to_num(depth_map, nan=0.0, posinf=0.0, neginf=0.0)
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    normalized = np.zeros_like(finite) if maximum <= minimum else (finite - minimum) / (maximum - minimum)
    return Image.fromarray((normalized * 255).astype(np.uint8))


def _font(image_height: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_size = max(28, min(64, image_height // 18))
    try:
        return ImageFont.truetype("arialbd.ttf", font_size)
    except OSError:
        return ImageFont.load_default(size=font_size)


def _pixel_bounds(box: YoloBox, image: Image.Image) -> tuple[int, int, int, int]:
    left, top, right, bottom = box.raw_bounds()
    return (
        round(left * image.width),
        round(top * image.height),
        round(right * image.width),
        round(bottom * image.height),
    )


def draw_marks(image: Image.Image, marks: Sequence[RegionMark]) -> Image.Image:
    marked = image.convert("RGB").copy()
    draw = ImageDraw.Draw(marked)
    font = _font(marked.height)
    occupied_badges: list[tuple[int, int, int, int]] = []
    for mark in marks:
        color = MARK_COLORS[(mark.mark_id - 1) % len(MARK_COLORS)]
        pixels = _pixel_bounds(mark.box, marked)
        line_width = max(5, marked.width // 140)
        draw.rectangle(pixels, outline=color, width=line_width)
        label = f"MARK {mark.mark_id}"
        label_box = draw.textbbox((0, 0), label, font=font, stroke_width=2)
        label_width = label_box[2] - label_box[0] + 18
        label_height = label_box[3] - label_box[1] + 14
        badge = _badge_rectangle(
            BadgeRequest(
                mark_id=mark.mark_id,
                box_pixels=pixels,
                badge_size=(label_width, label_height),
                canvas_size=marked.size,
            ),
            occupied_badges,
        )
        occupied_badges.append(badge)
        label_left, label_top = badge[0], badge[1]
        draw.rectangle(
            badge,
            fill=color,
            outline=(0, 0, 0),
            width=3,
        )
        draw.text(
            (label_left + 9, label_top + 5),
            label,
            fill=(255, 255, 255),
            font=font,
            stroke_width=2,
            stroke_fill=(0, 0, 0),
        )
    return marked


def draw_audit_boxes(image: Image.Image, boxes: Sequence[YoloBox]) -> Image.Image:
    audited = image.convert("RGB").copy()
    draw = ImageDraw.Draw(audited)
    font = _font(audited.height)
    for index, box in enumerate(boxes, start=1):
        pixels = _pixel_bounds(box, audited)
        color = MARK_COLORS[(index - 1) % len(MARK_COLORS)]
        draw.rectangle(pixels, outline=color, width=max(4, audited.width // 180))
        draw.text(
            (pixels[0] + 4, pixels[1] + 4),
            CLASS_NAMES[box.class_id],
            fill=(255, 255, 255),
            font=font,
            stroke_width=3,
            stroke_fill=(0, 0, 0),
        )
    return audited


def make_contact_sheet(paths: Sequence[Path], output_path: Path, cell_size: int = 420) -> None:
    columns = 3
    rows = math.ceil(len(paths) / columns)
    sheet = Image.new("RGB", (columns * cell_size, rows * cell_size), color=(245, 245, 245))
    for index, path in enumerate(paths):
        with Image.open(path) as opened:
            contained = ImageOps.contain(opened.convert("RGB"), (cell_size - 16, cell_size - 42))
        x = (index % columns) * cell_size + (cell_size - contained.width) // 2
        y = (index // columns) * cell_size + 34
        sheet.paste(contained, (x, y))
        ImageDraw.Draw(sheet).text(
            ((index % columns) * cell_size + 8, (index // columns) * cell_size + 8),
            path.stem,
            fill=(0, 0, 0),
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=90)
