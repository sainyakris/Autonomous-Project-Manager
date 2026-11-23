from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.models import ProjectStatus, TaskPriority, TaskStatus
from app.schemas.intake import Analysis


class AnalyzeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10, max_length=5000)


class AnalyzeResponse(Analysis):
    ready: bool  # computed by the server from clarity_score


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    # question text -> the user's answer
    answers: dict[str, str] = Field(default_factory=dict)

    @field_validator("answers")
    @classmethod
    def limit_answers(cls, v: dict[str, str]) -> dict[str, str]:
        if len(v) > 10:
            raise ValueError("at most 10 answers")
        for q, a in v.items():
            if len(q) > 300 or len(a) > 1000:
                raise ValueError("answer or question too long")
        return v


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    estimated_hours: float | None
    position: int
    depends_on: list[str] = Field(default_factory=list)  # real task ids


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    status: ProjectStatus
    summary: str | None
    risk_level: str | None
    created_at: datetime


class ProjectDetail(ProjectOut):
    tasks: list[TaskOut]