from __future__ import annotations

import re
from typing import Final, assert_never

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from prototypes.depth_guided_roi_v3.protocol import MarkAnswer, MarkedResponse


class ObjectsMapResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    priority_mark_id: int = Field(ge=1, le=3)
    objects: dict[str, str]


class MarksMapResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    priority_mark_id: int = Field(ge=1, le=3)
    marks: dict[str, str]


class MarksWithoutDescriptionResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    priority_mark_id: int = Field(ge=1, le=3)
    marks: tuple[MarkAnswer, ...] = Field(min_length=1, max_length=3)


class ObjectsListResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    priority_mark_id: int = Field(ge=1, le=3)
    objects: tuple[MarkAnswer, ...] = Field(min_length=1, max_length=3)


class FlatMarkResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    __pydantic_extra__: dict[str, str] = Field(init=False)
    priority_mark_id: int | str


RouterResponse = (
    MarkedResponse
    | ObjectsMapResponse
    | MarksMapResponse
    | MarksWithoutDescriptionResponse
    | ObjectsListResponse
    | FlatMarkResponse
)
ROUTER_RESPONSE_ADAPTER: Final = TypeAdapter(RouterResponse)
MARK_KEY_PATTERN: Final = re.compile(r"^MARK ([1-3])$")
FLEXIBLE_MARK_KEY_PATTERN: Final = re.compile(r"^(?:MARK )?([1-3])$")


class StrongModelProtocolError(RuntimeError):
    reason: str

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _priority_id(value: int | str) -> int:
    match value:
        case int() as mark_id if 1 <= mark_id <= 3:
            return mark_id
        case str() as label:
            match_result = MARK_KEY_PATTERN.fullmatch(label)
            if match_result is None:
                raise StrongModelProtocolError(f"Invalid priority mark label: {label}")
            return int(match_result.group(1))
        case unreachable:
            assert_never(unreachable)


def _answers_from_mapping(entries: dict[str, str], key_pattern: re.Pattern[str]) -> tuple[MarkAnswer, ...]:
    answers: list[MarkAnswer] = []
    for key, value in entries.items():
        match_result = key_pattern.fullmatch(key)
        if match_result is None:
            continue
        answers.append(MarkAnswer(id=int(match_result.group(1)), object=value))
    return tuple(sorted(answers, key=lambda answer: answer.mark_id))


def parse_marked_response(content: str) -> MarkedResponse:
    try:
        parsed = ROUTER_RESPONSE_ADAPTER.validate_json(content)
    except ValidationError as exc:
        raise StrongModelProtocolError("Router returned an unsupported marked-response shape.") from exc
    match parsed:
        case MarkedResponse():
            return parsed
        case ObjectsMapResponse(priority_mark_id=priority_mark_id, objects=objects):
            answers = _answers_from_mapping(objects, re.compile(r"^([1-3])$"))
        case MarksMapResponse(priority_mark_id=priority_mark_id, marks=marks):
            answers = _answers_from_mapping(marks, re.compile(r"^([1-3])$"))
        case MarksWithoutDescriptionResponse(priority_mark_id=priority_mark_id, marks=answers):
            pass
        case ObjectsListResponse(priority_mark_id=priority_mark_id, objects=answers):
            pass
        case FlatMarkResponse(priority_mark_id=priority, __pydantic_extra__=extra):
            priority_mark_id = _priority_id(priority)
            answers = _answers_from_mapping(extra, FLEXIBLE_MARK_KEY_PATTERN)
        case unreachable:
            assert_never(unreachable)
    if not answers:
        raise StrongModelProtocolError("Router response did not contain any recognized MARK answers.")
    return MarkedResponse(
        marks=answers,
        priority_mark_id=priority_mark_id,
        description="Normalized router response; description was not returned.",
    )
