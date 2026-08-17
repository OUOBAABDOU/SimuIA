from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.modules.interviews.models import AnswerType


class InterviewCreate(BaseModel):
    simulation_id: UUID


class InterviewRead(BaseModel):
    id: UUID
    simulation_id: UUID
    status: Literal["CREATED", "ACTIVE", "COMPLETED", "ABORTED"]


class InterviewDecision(BaseModel):
    action: Literal["NEXT_QUESTION", "FINISH"]
    question: str | None = None
    reason: str
    completion_score: float = Field(ge=0, le=100)


class AnswerCreate(BaseModel):
    text: str | None = Field(default=None, max_length=20000)
    answer_type: AnswerType = AnswerType.TEXT
    recording_id: UUID | None = None
    duration_seconds: int | None = Field(default=None, ge=0, le=7200)

    @model_validator(mode="after")
    def validate_answer_payload(self) -> "AnswerCreate":
        if self.answer_type == AnswerType.TEXT:
            if not self.text or not self.text.strip() or self.recording_id is not None:
                raise ValueError("TEXT answers require text and must not include recording_id")
        elif self.recording_id is None:
            raise ValueError("AUDIO and VIDEO answers require recording_id")
        return self
