from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class HandEnum(str, Enum):
    left = "Left"
    right = "Right"
    none = "None"


class CompletionStatus(str, Enum):
    completed = "completed"
    failed = "failed"
    aborted = "aborted"


class EventIn(BaseModel):
    event_id: UUID
    participant_id: str
    study_id: str
    condition_id: str
    task_id: str
    event_type: str
    object_id: str | None = None
    tool_id: str | None = None
    hand: HandEnum = HandEnum.none
    timestamp_utc: datetime
    time_since_session_start_ms: int = Field(ge=0)
    position: dict[str, float] | None = None
    rotation: dict[str, float] | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class SessionSummaryIn(BaseModel):
    participant_id: str
    study_id: str
    condition_id: str
    session_id: str
    start_time_utc: datetime
    duration_sec: float = Field(gt=0)
    completion_status: CompletionStatus
    total_errors: int = Field(ge=0)
    hints_used: int = Field(ge=0)
    task_completion_time_sec: float = Field(ge=0)
    score: float | None = None


class SessionUpload(BaseModel):
    session_summary: SessionSummaryIn
    events: list[EventIn]

    @field_validator("events")
    @classmethod
    def events_not_empty(cls, value: list[EventIn]) -> list[EventIn]:
        if not value:
            raise ValueError("At least one event is required")
        return value


class ExclusionRule(BaseModel):
    rule_name: str
    params: dict[str, float | int | str]


class AnalysisRequest(BaseModel):
    study_id: str
    dependent_variable: str = "task_completion_time_sec"
    group_variable: str = "condition_id"
    test_type: str = "auto"
    auto_normality: bool = True
    exclusions: list[ExclusionRule] = Field(default_factory=list)
