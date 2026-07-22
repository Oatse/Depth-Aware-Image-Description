import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

import anyio
from anyio import WouldBlock
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from services.analysis_types import AnalysisMode


logger = logging.getLogger(__name__)


class AnalysisJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisQueueFullError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AnalysisJobRequest:
    image_bytes: bytes
    filename: str
    content_type: str
    width: int
    height: int
    mode: AnalysisMode
    save_result: bool
    capture_id: str | None = None
    capture_time_ms: int | None = None
    camera_facing_mode: str | None = None
    sensor_evidence: dict[str, object] | None = None
    stored_capture_id: str | None = None
    source_image: dict[str, str] | None = None


@dataclass(slots=True)
class AnalysisJobRecord:
    job_id: str
    request: AnalysisJobRequest
    status: AnalysisJobStatus
    created_at: str
    updated_at: str
    result: dict[str, object] | None = None
    error: str | None = None


JobRunner = Callable[[AnalysisJobRequest], Awaitable[dict[str, object]]]


class AnalysisJobService:
    def __init__(
        self,
        runner: JobRunner,
        queue_capacity: int,
        retained_jobs: int,
    ) -> None:
        if queue_capacity < 1:
            raise ValueError("queue_capacity must be greater than 0")
        if retained_jobs < queue_capacity:
            raise ValueError("retained_jobs must be at least queue_capacity")
        sender, receiver = anyio.create_memory_object_stream[str](queue_capacity)
        self._sender: MemoryObjectSendStream[str] = sender
        self._receiver: MemoryObjectReceiveStream[str] = receiver
        self._runner = runner
        self._retained_jobs = retained_jobs
        self._jobs: dict[str, AnalysisJobRecord] = {}

    def enqueue(self, request: AnalysisJobRequest, *, job_id: str | None = None) -> AnalysisJobRecord:
        self._trim_terminal_jobs()
        now = _utc_now()
        record = AnalysisJobRecord(
            job_id=job_id or uuid4().hex,
            request=request,
            status=AnalysisJobStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )
        self._jobs[record.job_id] = record
        try:
            self._sender.send_nowait(record.job_id)
        except WouldBlock as exc:
            self._jobs.pop(record.job_id, None)
            raise AnalysisQueueFullError("Antrean analisis penuh. Coba lagi setelah pekerjaan aktif selesai.") from exc
        return record

    def get(self, job_id: str) -> AnalysisJobRecord | None:
        return self._jobs.get(job_id)

    async def serve(self) -> None:
        async with self._receiver:
            async for job_id in self._receiver:
                await self._run_job(job_id)

    async def close(self) -> None:
        await self._sender.aclose()

    async def _run_job(self, job_id: str) -> None:
        record = self._jobs.get(job_id)
        if record is None:
            return
        record.status = AnalysisJobStatus.RUNNING
        record.updated_at = _utc_now()
        try:
            record.result = await self._runner(record.request)
            record.status = AnalysisJobStatus.COMPLETED
        except Exception as exc:
            record.error = str(exc)
            record.status = AnalysisJobStatus.FAILED
            logger.exception(
                "Analysis job failed: job_id=%s mode=%s error=%s",
                record.job_id,
                record.request.mode,
                exc,
            )
        record.updated_at = _utc_now()

    def _trim_terminal_jobs(self) -> None:
        overflow = len(self._jobs) - self._retained_jobs + 1
        if overflow <= 0:
            return
        terminal = [
            record
            for record in self._jobs.values()
            if record.status in {AnalysisJobStatus.COMPLETED, AnalysisJobStatus.FAILED}
        ]
        terminal.sort(key=lambda record: record.updated_at)
        for record in terminal[:overflow]:
            self._jobs.pop(record.job_id, None)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
