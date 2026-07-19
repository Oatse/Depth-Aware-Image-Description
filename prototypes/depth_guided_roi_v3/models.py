from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
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
    ("laptop", "notebook", "komputer jinjing", "komputer portabel"),
    ("wardrobe", "lemari pakaian", "lemari"),
    ("window", "jendela"),
    ("door", "pintu"),
    ("potted plant", "plant", "tanaman pot", "tanaman dalam pot", "tanaman"),
    ("photo frame", "bingkai foto", "bingkai gambar", "bingkai"),
)

class ExperimentCondition(StrEnum):
    BASELINE = "baseline"
    SOM_CONTROL = "som_control"
    DEPTH_GUIDED = "depth_guided"


class RejectionReason(StrEnum):
    CLIPPED = "clipped"
    BORDER_TOUCHING = "border_touching"
    SMALL_AREA = "small_area"
    SMALL_SIDE = "small_side"


class YoloBox(BaseModel):
    model_config = ConfigDict(frozen=True)

    class_id: int = Field(ge=0, le=11)
    center_x: float = Field(ge=0.0, le=1.0)
    center_y: float = Field(ge=0.0, le=1.0)
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)

    @property
    def area(self) -> float:
        return self.width * self.height

    def raw_bounds(self) -> tuple[float, float, float, float]:
        return (
            self.center_x - self.width / 2.0,
            self.center_y - self.height / 2.0,
            self.center_x + self.width / 2.0,
            self.center_y + self.height / 2.0,
        )


@dataclass(frozen=True, slots=True)
class RegionMark:
    mark_id: int
    box: YoloBox
    median_depth: float | None
    p10_depth: float | None


@dataclass(frozen=True, slots=True)
class DatasetSample:
    image_path: Path
    label_path: Path
    boxes: tuple[YoloBox, ...]


@dataclass(frozen=True, slots=True)
class DatasetAudit:
    scanned_images: int
    eligible_images: int
    rejected_clipped: int
    rejected_border_touching: int
    rejected_small_area: int
    rejected_small_side: int


@dataclass(frozen=True, slots=True)
class SampleSelection:
    samples: tuple[DatasetSample, ...]
    audit: DatasetAudit


@dataclass(frozen=True, slots=True)
class ExperimentPaths:
    dataset_root: Path
    output_root: Path


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    paths: ExperimentPaths
    image_limit: int
    marks_per_image: int
    max_relative_depth_spread: float


@dataclass(frozen=True, slots=True)
class ConditionObservation:
    image_name: str
    condition: ExperimentCondition
    structured_output_valid: bool
    mark_protocol_valid: bool
    expected_targets: int
    returned_targets: int
    matched_targets: int
    hallucinated_mark_ids: int
    latency_ms: int
    error: str | None


@dataclass(frozen=True, slots=True)
class MarkObservation:
    image_name: str
    condition: ExperimentCondition
    mark_id: int
    expected_class: str
    predicted_object: str
    object_match: bool
    median_depth: float | None
    p10_depth: float | None


@dataclass(frozen=True, slots=True)
class PreparedSample:
    sample: DatasetSample
    baseline_path: Path
    control_path: Path
    depth_guided_path: Path
    control_marks: tuple[RegionMark, ...]
    depth_marks: tuple[RegionMark, ...]


class StoredInference(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_name: str
    condition: ExperimentCondition
    content: str
    latency_ms: int = Field(ge=0)
