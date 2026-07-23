from __future__ import annotations

import json
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


CAPTURE_SCHEMA_VERSION = 1
CAPTURE_CANDIDATE_BATCH_ID = "capture-candidates"
CAPTURE_CANDIDATE_IMAGE_PREFIX = "images/capture_candidates"
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_ACTIVE_ANALYSIS_STATES = {"queued", "running"}


def incoming_capture_root(results_dir: Path) -> Path:
    return results_dir / "captures" / "incoming"


class CaptureRepositoryError(RuntimeError):
    pass


class CaptureAlreadyExistsError(CaptureRepositoryError):
    pass


class CaptureNotFoundError(CaptureRepositoryError):
    pass


class CaptureStateError(CaptureRepositoryError):
    pass


class CaptureRepository:
    _lock = threading.RLock()

    def __init__(self, root: Path) -> None:
        self.root = root
        self.images_dir = root / "images"
        self.records_dir = root / "records"

    def create(
        self,
        *,
        image_bytes: bytes,
        original_filename: str,
        content_type: str,
        width: int,
        height: int,
        capture_id: str | None,
        batch_id: str,
        capture_time_ms: int,
        camera_facing_mode: str | None,
        mode: str,
        sensor_evidence: dict[str, Any] | None,
        metadata: dict[str, Any] | None = None,
        image_path_prefix: str | None = None,
    ) -> dict[str, Any]:
        canonical_capture_id = self._validate_token(capture_id or uuid4().hex, "capture_id")
        canonical_batch_id = self._validate_token(batch_id, "batch_id")
        extension = self._safe_extension(original_filename, content_type)
        image_relative_path = self._image_path(image_path_prefix, canonical_capture_id, extension)
        image_path = self.root / image_relative_path
        record_path = self._record_path(canonical_capture_id)
        now = self._utc_now()
        record = {
            "schema_version": CAPTURE_SCHEMA_VERSION,
            "capture_id": canonical_capture_id,
            "batch_id": canonical_batch_id,
            "status": "captured",
            "capture_time_ms": capture_time_ms,
            "camera_facing_mode": camera_facing_mode,
            "mode": mode,
            "image": {
                "original_filename": original_filename,
                "content_type": content_type,
                "width": width,
                "height": height,
                "path": image_relative_path.as_posix(),
            },
            "sensor_evidence": sensor_evidence,
            "metadata": metadata or {},
            "analysis_attempts": 0,
            "analysis_job_id": None,
            "analysis_run_id": None,
            "analysis_error": None,
            "created_at": now,
            "updated_at": now,
        }
        with self._lock:
            if record_path.exists() or image_path.exists():
                raise CaptureAlreadyExistsError(f"Capture {canonical_capture_id} sudah tersimpan.")
            record_metadata = record["metadata"]
            ground_truth_cm = record_metadata.get("ground_truth_cm")
            if ground_truth_cm is not None and record_metadata.get("repeat_index") is None:
                record_metadata["repeat_index"] = self._next_repeat_index(
                    batch_id=canonical_batch_id,
                    ground_truth_cm=float(ground_truth_cm),
                    target_id=record_metadata.get("target_id"),
                )
            image_path.parent.mkdir(parents=True, exist_ok=True)
            self.records_dir.mkdir(parents=True, exist_ok=True)
            temporary_image = image_path.with_name(f".{image_path.name}.{uuid4().hex}.tmp")
            try:
                temporary_image.write_bytes(image_bytes)
                temporary_image.replace(image_path)
                self._write_record(record)
            except Exception:
                temporary_image.unlink(missing_ok=True)
                image_path.unlink(missing_ok=True)
                raise
        return record

    def get(self, capture_id: str) -> dict[str, Any]:
        canonical_capture_id = self._validate_token(capture_id, "capture_id")
        path = self._record_path(canonical_capture_id)
        with self._lock:
            if not path.exists():
                raise CaptureNotFoundError(f"Capture {canonical_capture_id} tidak ditemukan.")
            record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("schema_version") != CAPTURE_SCHEMA_VERSION:
            raise CaptureRepositoryError(
                f"Versi schema capture tidak didukung: {record.get('schema_version')}."
            )
        return record

    def list(
        self,
        *,
        batch_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        canonical_batch_id = self._validate_token(batch_id, "batch_id") if batch_id else None
        if not self.records_dir.exists():
            return []
        records: list[dict[str, Any]] = []
        with self._lock:
            paths = sorted(self.records_dir.glob("*.json"))
            for path in paths:
                record = json.loads(path.read_text(encoding="utf-8"))
                if record.get("schema_version") != CAPTURE_SCHEMA_VERSION:
                    raise CaptureRepositoryError(
                        f"Versi schema capture tidak didukung pada {path.name}."
                    )
                if canonical_batch_id and record.get("batch_id") != canonical_batch_id:
                    continue
                if status and record.get("status") != status:
                    continue
                records.append(record)
        records.sort(key=lambda item: (str(item.get("created_at", "")), str(item.get("capture_id", ""))))
        return records

    def count(self, *, batch_id: str | None = None, status: str | None = None) -> int:
        return len(self.list(batch_id=batch_id, status=status))

    def read_image(self, capture_id: str) -> bytes:
        record = self.get(capture_id)
        relative_path = Path(str(record.get("image", {}).get("path", "")))
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise CaptureRepositoryError("Path gambar capture tidak valid.")
        image_path = (self.root / relative_path).resolve()
        root = self.root.resolve()
        if not image_path.is_relative_to(root) or not image_path.is_file():
            raise CaptureRepositoryError("File gambar capture tidak ditemukan.")
        return image_path.read_bytes()

    def mark_queued(self, capture_id: str, *, job_id: str, mode: str, allow_completed: bool = False) -> dict[str, Any]:
        def mutate(record: dict[str, Any]) -> None:
            current = str(record.get("status", "captured"))
            if current in _ACTIVE_ANALYSIS_STATES:
                raise CaptureStateError(
                    f"Capture {capture_id} sedang dianalisis oleh job {record.get('analysis_job_id')}."
                )
            if current == "completed" and not allow_completed:
                raise CaptureStateError(f"Capture {capture_id} sudah selesai dianalisis.")
            record["status"] = "queued"
            record["mode"] = mode
            record["analysis_job_id"] = job_id
            record["analysis_run_id"] = None
            record["analysis_error"] = None
            record["analysis_attempts"] = int(record.get("analysis_attempts", 0)) + 1

        return self._update(capture_id, mutate)

    def mark_running(self, capture_id: str) -> dict[str, Any]:
        def mutate(record: dict[str, Any]) -> None:
            if record.get("status") != "queued":
                raise CaptureStateError(
                    f"Capture {capture_id} tidak dapat dijalankan dari status {record.get('status')}."
                )
            record["status"] = "running"

        return self._update(capture_id, mutate)

    def mark_completed(self, capture_id: str, *, analysis_run_id: str) -> dict[str, Any]:
        def mutate(record: dict[str, Any]) -> None:
            if record.get("status") not in _ACTIVE_ANALYSIS_STATES:
                raise CaptureStateError(
                    f"Capture {capture_id} tidak dapat diselesaikan dari status {record.get('status')}."
                )
            record["status"] = "completed"
            record["analysis_run_id"] = analysis_run_id
            record["analysis_error"] = None

        return self._update(capture_id, mutate)

    def mark_failed(self, capture_id: str, *, error: str) -> dict[str, Any]:
        def mutate(record: dict[str, Any]) -> None:
            if record.get("status") not in _ACTIVE_ANALYSIS_STATES:
                return
            record["status"] = "failed"
            record["analysis_error"] = error

        return self._update(capture_id, mutate)

    def recover_orphaned_analysis(self, capture_id: str) -> dict[str, Any]:
        def mutate(record: dict[str, Any]) -> None:
            if record.get("status") not in _ACTIVE_ANALYSIS_STATES:
                raise CaptureStateError(
                    f"Capture {capture_id} tidak mempunyai job aktif yang perlu dipulihkan."
                )
            record["status"] = "failed"
            record["analysis_error"] = "Job sebelumnya tidak tersedia setelah backend restart."

        return self._update(capture_id, mutate)

    def update_experiment_metadata(
        self,
        capture_id: str,
        *,
        ground_truth_cm: float,
        camera_sensor_offset_cm: float,
        repeat_index: int,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        if ground_truth_cm <= camera_sensor_offset_cm:
            raise CaptureRepositoryError(
                "ground_truth_cm harus lebih besar daripada offset kamera-sensor."
            )
        if repeat_index < 1:
            raise CaptureRepositoryError("repeat_index harus lebih besar dari nol.")

        def mutate(record: dict[str, Any]) -> None:
            metadata = record.setdefault("metadata", {})
            metadata.update({
                "camera_sensor_offset_cm": camera_sensor_offset_cm,
                "ground_truth_cm": ground_truth_cm,
                "sensor_face_ground_truth_cm": ground_truth_cm - camera_sensor_offset_cm,
                "target_id": target_id,
                "repeat_index": repeat_index,
            })

        return self._update(capture_id, mutate)

    def public_source_image(self, capture_id: str) -> dict[str, str]:
        record = self.get(capture_id)
        image_path = str(record["image"]["path"])
        public_path = (Path("captures") / image_path).as_posix()
        return {"path": public_path, "url": f"/results/{public_path}"}

    def _update(self, capture_id: str, mutate) -> dict[str, Any]:
        canonical_capture_id = self._validate_token(capture_id, "capture_id")
        with self._lock:
            record = self.get(canonical_capture_id)
            mutate(record)
            record["updated_at"] = self._utc_now()
            self._write_record(record)
            return record

    def _write_record(self, record: dict[str, Any]) -> None:
        self.records_dir.mkdir(parents=True, exist_ok=True)
        path = self._record_path(str(record["capture_id"]))
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def _next_repeat_index(
        self,
        *,
        batch_id: str,
        ground_truth_cm: float,
        target_id: str | None,
    ) -> int:
        highest = 0
        if not self.records_dir.exists():
            return 1
        for path in self.records_dir.glob("*.json"):
            existing = json.loads(path.read_text(encoding="utf-8"))
            metadata = existing.get("metadata") or {}
            if existing.get("batch_id") != batch_id:
                continue
            if metadata.get("ground_truth_cm") is None:
                continue
            if float(metadata["ground_truth_cm"]) != ground_truth_cm:
                continue
            if metadata.get("target_id") != target_id:
                continue
            highest = max(highest, int(metadata.get("repeat_index") or 0))
        return highest + 1

    def _record_path(self, capture_id: str) -> Path:
        return self.records_dir / f"{capture_id}.json"

    @classmethod
    def _image_path(cls, prefix: str | None, capture_id: str, extension: str) -> Path:
        if prefix is None or not prefix.strip():
            return Path("images") / f"{capture_id}{extension}"
        relative = Path(prefix.strip().replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise CaptureRepositoryError("image_path_prefix tidak valid.")
        if relative.parts[0] != "images" or any(not _SAFE_TOKEN.fullmatch(part) for part in relative.parts):
            raise CaptureRepositoryError(
                "image_path_prefix harus berada di bawah images/ dan memakai token aman."
            )
        return relative / f"{capture_id}{extension}"

    @staticmethod
    def _validate_token(value: str, field_name: str) -> str:
        if not _SAFE_TOKEN.fullmatch(value):
            raise CaptureRepositoryError(
                f"{field_name} hanya boleh berisi huruf, angka, tanda hubung, atau garis bawah."
            )
        return value

    @staticmethod
    def _safe_extension(filename: str, content_type: str) -> str:
        by_content_type = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }
        if content_type in by_content_type:
            return by_content_type[content_type]
        suffix = Path(filename).suffix.lower()
        return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).isoformat()
