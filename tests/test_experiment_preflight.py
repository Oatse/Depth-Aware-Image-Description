from pathlib import Path

import pytest

from app.config import Settings
from services.experiment_preflight import (
    ExperimentPreflightConfig,
    ExperimentPreflightError,
    run_experiment_preflight,
)


ANNOTATION_HEADER = (
    "image_name,main_object,object_position,distance_annotation_basis,"
    "annotation_confidence,distance_category,has_obstacle,front_area_status,"
    "safer_direction,notes\n"
)


def _write_annotation(path: Path, image_name: str) -> None:
    path.write_text(
        ANNOTATION_HEADER
        + f"{image_name},kursi,tengah,visual_relative,medium,dekat,yes,potensi_halangan,kanan,kursi di depan\n",
        encoding="utf-8",
    )


def test_preflight_rejects_empty_image_directory(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    annotations_path = tmp_path / "annotations.csv"
    _write_annotation(annotations_path, "img_001.jpg")

    config = ExperimentPreflightConfig(
        images_dir=images_dir,
        annotations_path=annotations_path,
        modes=("gemma_depth",),
    )

    with pytest.raises(ExperimentPreflightError) as error:
        run_experiment_preflight(config, Settings(depth_mock=True, gemma_mock=True))

    assert "Tidak ada gambar eksperimen" in str(error.value)


def test_preflight_rejects_annotation_image_mismatch(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "sample.jpg").write_bytes(b"not-used")
    annotations_path = tmp_path / "annotations.csv"
    _write_annotation(annotations_path, "other.jpg")

    config = ExperimentPreflightConfig(
        images_dir=images_dir,
        annotations_path=annotations_path,
        modes=("gemma_depth",),
        allow_mock=True,
    )

    with pytest.raises(ExperimentPreflightError) as error:
        run_experiment_preflight(config, Settings(depth_mock=True, gemma_mock=True))

    message = str(error.value)
    assert "Gambar belum punya anotasi: sample.jpg" in message
    assert "Anotasi tidak punya file gambar: other.jpg" in message


def test_preflight_rejects_mock_runtime_without_explicit_allowance(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img_001.jpg").write_bytes(b"not-used")
    annotations_path = tmp_path / "annotations.csv"
    _write_annotation(annotations_path, "img_001.jpg")

    config = ExperimentPreflightConfig(
        images_dir=images_dir,
        annotations_path=annotations_path,
        modes=("gemma_depth",),
    )

    with pytest.raises(ExperimentPreflightError) as error:
        run_experiment_preflight(config, Settings(depth_mock=True, gemma_mock=True))

    assert "Mock runtime aktif" in str(error.value)


def test_preflight_returns_report_for_valid_mock_development_run(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img_001.jpg").write_bytes(b"not-used")
    annotations_path = tmp_path / "annotations.csv"
    _write_annotation(annotations_path, "img_001.jpg")

    config = ExperimentPreflightConfig(
        images_dir=images_dir,
        annotations_path=annotations_path,
        modes=("gemma_depth",),
        allow_mock=True,
    )

    report = run_experiment_preflight(config, Settings(depth_mock=True, gemma_mock=True))

    assert report.image_count == 1
    assert report.annotation_count == 1
    assert report.mock_enabled is True


def test_preflight_rejects_non_visual_relative_distance_basis(tmp_path: Path) -> None:
    # Given
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img_001.jpg").write_bytes(b"not-used")
    annotations_path = tmp_path / "annotations.csv"
    annotations_path.write_text(
        ANNOTATION_HEADER
        + "img_001.jpg,kursi,tengah,meter_manual,medium,dekat,yes,potensi_halangan,kanan,catatan\n",
        encoding="utf-8",
    )
    config = ExperimentPreflightConfig(
        images_dir=images_dir,
        annotations_path=annotations_path,
        modes=("gemma_depth",),
        allow_mock=True,
    )

    # When / Then
    with pytest.raises(ExperimentPreflightError, match="distance_annotation_basis harus visual_relative"):
        run_experiment_preflight(config, Settings(depth_mock=True, gemma_mock=True))


def test_preflight_rejects_unverifiable_metric_ground_truth_column(tmp_path: Path) -> None:
    # Given
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "img_001.jpg").write_bytes(b"not-used")
    annotations_path = tmp_path / "annotations.csv"
    annotations_path.write_text(
        ANNOTATION_HEADER.rstrip("\n")
        + ",distance_meter\n"
        + "img_001.jpg,kursi,tengah,visual_relative,medium,dekat,yes,potensi_halangan,kanan,catatan,1.2\n",
        encoding="utf-8",
    )
    config = ExperimentPreflightConfig(
        images_dir=images_dir,
        annotations_path=annotations_path,
        modes=("gemma_depth",),
        allow_mock=True,
    )

    # When / Then
    with pytest.raises(ExperimentPreflightError, match="Kolom jarak fisik tidak diizinkan"):
        run_experiment_preflight(config, Settings(depth_mock=True, gemma_mock=True))
