import csv
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from services.evaluator import REQUIRED_ANNOTATION_COLUMNS


IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
EXPERIMENT_MODES = frozenset({"gemma_only", "depth_only", "gemma_depth", "gemma_depth_prompted"})
GEMMA_MODES = frozenset({"gemma_only", "gemma_depth", "gemma_depth_prompted"})
DEPTH_MODES = frozenset({"depth_only", "gemma_depth", "gemma_depth_prompted"})


@dataclass(frozen=True, slots=True)
class ExperimentPreflightConfig:
    images_dir: Path
    annotations_path: Path
    modes: tuple[str, ...]
    allow_mock: bool = False


@dataclass(frozen=True, slots=True)
class ExperimentPreflightReport:
    image_count: int
    annotation_count: int
    modes: tuple[str, ...]
    mock_enabled: bool
    depth_model_status: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AnnotationIndex:
    image_names: frozenset[str]
    columns: frozenset[str]

    @property
    def count(self) -> int:
        return len(self.image_names)


class ExperimentPreflightError(RuntimeError):
    def __init__(self, errors: tuple[str, ...]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


def run_experiment_preflight(config: ExperimentPreflightConfig, settings: Settings) -> ExperimentPreflightReport:
    image_names = _collect_image_names(config.images_dir)
    annotation_index = _read_annotation_index(config.annotations_path)
    errors = [
        *_validate_dataset_files(config, image_names, annotation_index),
        *_validate_runtime_config(config, settings),
    ]
    if errors:
        raise ExperimentPreflightError(tuple(errors))

    return ExperimentPreflightReport(
        image_count=len(image_names),
        annotation_count=annotation_index.count,
        modes=config.modes,
        mock_enabled=settings.gemma_mock or settings.depth_mock,
        depth_model_status=settings.depth_model_status,
        warnings=_build_warnings(config, settings),
    )


def _collect_image_names(images_dir: Path) -> frozenset[str]:
    if not images_dir.exists() or not images_dir.is_dir():
        return frozenset()
    return frozenset(
        path.name
        for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def _read_annotation_index(annotations_path: Path) -> AnnotationIndex:
    if not annotations_path.exists():
        return AnnotationIndex(frozenset(), frozenset())

    with annotations_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = frozenset(reader.fieldnames or ())

    return AnnotationIndex(
        image_names=frozenset(row.get("image_name", "") for row in rows if row.get("image_name")),
        columns=columns,
    )


def _validate_dataset_files(
    config: ExperimentPreflightConfig,
    image_names: frozenset[str],
    annotation_index: AnnotationIndex,
) -> tuple[str, ...]:
    errors: list[str] = []
    if not image_names:
        errors.append(f"Tidak ada gambar eksperimen di {config.images_dir}.")
    if not config.annotations_path.exists():
        errors.append(f"File anotasi tidak ditemukan: {config.annotations_path}.")
        return tuple(errors)

    missing_columns = REQUIRED_ANNOTATION_COLUMNS - annotation_index.columns
    if missing_columns:
        errors.append(f"Kolom anotasi kurang: {', '.join(sorted(missing_columns))}.")
    if annotation_index.count == 0:
        errors.append(f"File anotasi belum memiliki baris data: {config.annotations_path}.")

    images_without_annotations = sorted(image_names - annotation_index.image_names)
    annotations_without_images = sorted(annotation_index.image_names - image_names)
    if images_without_annotations:
        errors.append(f"Gambar belum punya anotasi: {', '.join(images_without_annotations)}.")
    if annotations_without_images:
        errors.append(f"Anotasi tidak punya file gambar: {', '.join(annotations_without_images)}.")
    return tuple(errors)


def _validate_runtime_config(config: ExperimentPreflightConfig, settings: Settings) -> tuple[str, ...]:
    errors: list[str] = []
    uses_gemma = any(mode in GEMMA_MODES for mode in config.modes)
    uses_depth = any(mode in DEPTH_MODES for mode in config.modes)

    if not config.allow_mock and ((uses_gemma and settings.gemma_mock) or (uses_depth and settings.depth_mock)):
        errors.append("Mock runtime aktif. Gunakan --allow-mock hanya untuk dry run, bukan eksperimen final.")
    if uses_depth and settings.depth_model_status == "disabled":
        errors.append("Depth estimation nonaktif, tetapi mode eksperimen membutuhkan depth.")
    if uses_depth and settings.depth_model_status == "error":
        errors.append(f"Depth model tidak ditemukan di {settings.depth_model_path}.")
    return tuple(errors)


def _build_warnings(config: ExperimentPreflightConfig, settings: Settings) -> tuple[str, ...]:
    warnings: list[str] = []
    uses_gemma = any(mode in GEMMA_MODES for mode in config.modes)
    uses_depth = any(mode in DEPTH_MODES for mode in config.modes)
    if config.allow_mock and ((uses_gemma and settings.gemma_mock) or (uses_depth and settings.depth_mock)):
        warnings.append("Run ini memakai mock dan tidak boleh dijadikan hasil eksperimen final.")
    return tuple(warnings)
