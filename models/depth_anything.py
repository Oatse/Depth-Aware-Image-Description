import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import numpy as np
from PIL import Image

from app.config import Settings


@dataclass(frozen=True)
class DepthResult:
    success: bool
    depth_map: np.ndarray | None
    depth_map_path: str | None
    latency_ms: int
    depth_shape: tuple[int, int] | None
    mock: bool = False
    error: str | None = None


class DepthAnything:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._session = None

    def estimate(self, image: Image.Image, source_name: str) -> DepthResult:
        started_at = time.perf_counter()
        if not self.settings.enable_depth_estimation:
            return DepthResult(False, None, None, 0, None, error="Depth estimation is disabled.")

        if self.settings.depth_mock:
            depth_map = _mock_depth_map(image.height, image.width)
            path = self._save_depth_map(depth_map, source_name) if self.settings.save_depth_map else None
            return DepthResult(
                success=True,
                depth_map=depth_map,
                depth_map_path=path,
                latency_ms=_elapsed_ms(started_at),
                depth_shape=depth_map.shape,
                mock=True,
            )

        model_path = self._find_onnx_model()
        if model_path is None:
            return DepthResult(
                success=False,
                depth_map=None,
                depth_map_path=None,
                latency_ms=_elapsed_ms(started_at),
                depth_shape=None,
                error=f"Depth model not found in {self.settings.depth_model_path}.",
            )

        try:
            session = self._get_session(model_path)
            input_info = session.get_inputs()[0]
            input_name = input_info.name
            tensor = _prepare_onnx_input(image, self.settings.depth_input_size, input_info.shape)
            outputs = session.run(None, {input_name: tensor})
            depth_map = _normalize_output(outputs[0])
            path = self._save_depth_map(depth_map, source_name) if self.settings.save_depth_map else None
            return DepthResult(
                success=True,
                depth_map=depth_map,
                depth_map_path=path,
                latency_ms=_elapsed_ms(started_at),
                depth_shape=depth_map.shape,
            )
        except Exception as exc:
            return DepthResult(
                success=False,
                depth_map=None,
                depth_map_path=None,
                latency_ms=_elapsed_ms(started_at),
                depth_shape=None,
                error=f"Depth inference failed: {exc}",
            )

    def _find_onnx_model(self) -> Path | None:
        model_dir = self.settings.depth_model_path
        if model_dir.is_file() and model_dir.suffix == ".onnx":
            return model_dir
        if not model_dir.exists():
            return None
        candidates = sorted(model_dir.glob("*.onnx"))
        return candidates[0] if candidates else None

    def _get_session(self, model_path: Path):
        if self._session is None:
            import onnxruntime as ort

            self._session = ort.InferenceSession(
                str(model_path),
                providers=["CPUExecutionProvider"],
            )
        return self._session

    def _save_depth_map(self, depth_map: np.ndarray, source_name: str) -> str:
        output_dir = self.settings.results_dir / "depth_maps"
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_stem = Path(source_name).stem.replace(" ", "_") or "image"
        output_path = output_dir / f"{safe_stem}_{uuid4().hex[:8]}_depth.png"
        visual = _depth_to_uint8(depth_map)
        Image.fromarray(visual).save(output_path)
        return str(output_path.as_posix())


def _prepare_onnx_input(image: Image.Image, input_size: int, input_shape: list[int | str | None]) -> np.ndarray:
    resized = image.convert("RGB").resize((input_size, input_size), Image.Resampling.BILINEAR)
    array = np.asarray(resized, dtype=np.float32) / 255.0
    array = (array - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array(
        [0.229, 0.224, 0.225],
        dtype=np.float32,
    )
    channels_first = np.transpose(array, (2, 0, 1))[None, :, :, :]
    if len(input_shape) == 4 and input_shape[-1] == 3:
        return array[None, :, :, :].astype(np.float32)
    return channels_first.astype(np.float32)


def _normalize_output(output: np.ndarray) -> np.ndarray:
    depth = np.asarray(output, dtype=np.float32).squeeze()
    if depth.ndim != 2:
        raise ValueError(f"Unexpected depth output shape: {output.shape}")
    return depth


def _mock_depth_map(height: int, width: int) -> np.ndarray:
    y_axis = np.linspace(2.5, 0.4, max(height, 1), dtype=np.float32)
    return np.repeat(y_axis[:, None], max(width, 1), axis=1)


def _depth_to_uint8(depth_map: np.ndarray) -> np.ndarray:
    finite = np.nan_to_num(depth_map, nan=0.0, posinf=0.0, neginf=0.0)
    min_value = float(np.min(finite))
    max_value = float(np.max(finite))
    if max_value <= min_value:
        return np.zeros_like(finite, dtype=np.uint8)
    normalized = (finite - min_value) / (max_value - min_value)
    return (normalized * 255).astype(np.uint8)


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)
