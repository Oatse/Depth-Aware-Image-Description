from __future__ import annotations

from typing import Sequence, assert_never

from pydantic import BaseModel, ConfigDict, Field

from prototypes.depth_guided_roi_v3.models import ExperimentCondition


class BaselineResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    objects: tuple[str, ...] = Field(min_length=1, max_length=12)
    description: str = Field(min_length=1, max_length=500)


class MarkAnswer(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    mark_id: int = Field(alias="id", ge=1, le=3)
    object_name: str = Field(alias="object", min_length=1, max_length=80)


class MarkedResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    marks: tuple[MarkAnswer, ...] = Field(min_length=1, max_length=3)
    priority_mark_id: int = Field(ge=1, le=3)
    description: str = Field(min_length=1, max_length=500)


def has_exact_mark_ids(response: MarkedResponse, expected_ids: Sequence[int]) -> bool:
    returned_ids = tuple(answer.mark_id for answer in response.marks)
    return len(returned_ids) == len(set(returned_ids)) and set(returned_ids) == set(expected_ids)


def prompt_for(condition: ExperimentCondition, mark_ids: Sequence[int] = ()) -> str:
    match condition:
        case ExperimentCondition.BASELINE:
            return (
                "Amati gambar indoor asli tanpa metadata depth. Sebutkan objek yang terlihat jelas dan buat deskripsi visual "
                "ringkas dalam Bahasa Indonesia. Jangan mengklaim jarak, depth, atau area aman. Balas sesuai JSON schema."
            )
        case ExperimentCondition.SOM_CONTROL:
            ids = ", ".join(str(mark_id) for mark_id in mark_ids)
            return (
                f"Identifikasi hanya objek di dalam kotak MARK {ids}. Nomor adalah ID region dan tidak menyatakan depth. "
                "Isi tepat satu objek untuk setiap ID. priority_mark_id adalah region yang paling penting secara visual. "
                "Jangan membuat ID baru dan balas sesuai JSON schema."
            )
        case ExperimentCondition.DEPTH_GUIDED:
            ids = ", ".join(str(mark_id) for mark_id in mark_ids)
            return (
                f"Identifikasi hanya objek di dalam kotak MARK {ids}. Region telah dipilih menggunakan estimasi depth monokular "
                "dan nomor diurutkan dari estimasi relatif lebih dekat ke lebih jauh, sehingga MARK 1 diprioritaskan. "
                "Ini bukan jarak absolut. Isi tepat satu objek untuk setiap ID, set priority_mark_id ke 1, jangan membuat ID baru, "
                "dan balas sesuai JSON schema."
            )
        case unreachable:
            assert_never(unreachable)
