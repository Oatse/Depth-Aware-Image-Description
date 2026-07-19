from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field


CLASS_NAMES: Final = (
    "bed",
    "sofa",
    "chair",
    "table",
    "lamp",
    "tv",
    "laptop",
    "wardrobe",
    "window",
    "door",
    "potted plant",
    "photo frame",
)
CLASS_TERMS: Final = (
    ("bed", "tempat tidur", "ranjang", "kasur"),
    ("sofa", "couch"),
    ("chair", "kursi"),
    ("table", "meja"),
    ("lamp", "lampu"),
    ("tv", "televisi"),
    ("laptop", "komputer portabel"),
    ("wardrobe", "lemari pakaian", "lemari"),
    ("window", "jendela"),
    ("door", "pintu"),
    ("potted plant", "tanaman pot", "tanaman dalam pot", "tanaman"),
    ("photo frame", "bingkai foto", "bingkai gambar", "bingkai"),
)
MARK_COLORS: Final = ((239, 68, 68), (245, 158, 11), (6, 182, 212))


@dataclass(frozen=True, slots=True)
class AnnotationFormatError(Exception):
    path: Path
    line_number: int
    content: str

    def __str__(self) -> str:
        return f"Malformed YOLO annotation at {self.path}:{self.line_number}: {self.content!r}"


@dataclass(frozen=True, slots=True)
class DepthShapeError(Exception):
    shape: tuple[int, ...]

    def __str__(self) -> str:
        return f"Expected a two-dimensional depth map, received shape {self.shape}."


class YoloBox(BaseModel):
    model_config = ConfigDict(frozen=True)

    class_id: int = Field(ge=0, lt=len(CLASS_NAMES))
    center_x: float = Field(ge=0.0, le=1.0)
    center_y: float = Field(ge=0.0, le=1.0)
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)

    def bounds(self) -> tuple[float, float, float, float]:
        half_width = self.width / 2.0
        half_height = self.height / 2.0
        return (
            max(0.0, self.center_x - half_width),
            max(0.0, self.center_y - half_height),
            min(1.0, self.center_x + half_width),
            min(1.0, self.center_y + half_height),
        )


class MarkAnswer(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    mark_id: int = Field(alias="id", ge=1, le=3)
    object_name: str = Field(alias="object", min_length=1, max_length=80)


class MarkResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    marks: tuple[MarkAnswer, ...]
    description: str = Field(default="", max_length=500)


@dataclass(frozen=True, slots=True)
class PrototypeSample:
    image_path: Path
    label_path: Path
    boxes: tuple[YoloBox, ...]


@dataclass(frozen=True, slots=True)
class RankedMark:
    mark_id: int
    box: YoloBox
    median_depth: float
    p10_depth: float


@dataclass(frozen=True, slots=True)
class MarkResultRow:
    image_name: str
    mark_id: int
    expected_class: str
    predicted_object: str
    object_match: bool
    median_depth: float
    p10_depth: float
    gemma_latency_ms: int
    audit_status: str


@dataclass(frozen=True, slots=True)
class PrototypeTotals:
    selected_images: int
    completed_images: int
    expected_marks: int
    returned_marks: int
    matched_marks: int
    hallucinated_mark_ids: int
    latencies: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class PrototypeSummary:
    selected_images: int
    completed_images: int
    expected_marks: int
    returned_marks: int
    matched_marks: int
    hallucinated_mark_ids: int
    image_coverage: float
    mark_coverage: float
    object_accuracy: float
    mean_gemma_latency_ms: float
    gate_passed: bool
    gate_reason: str


@dataclass(frozen=True, slots=True)
class CheckpointState:
    processed_images: int
    total_images: int
    persisted_mark_rows: int


@dataclass(frozen=True, slots=True)
class ImageState:
    index: int
    total: int
    image_name: str
    marks: tuple[RankedMark, ...]
    answers: dict[int, str]


@dataclass(frozen=True, slots=True)
class PrototypeRuntimeError(Exception):
    reason: str

    def __str__(self) -> str:
        return self.reason
