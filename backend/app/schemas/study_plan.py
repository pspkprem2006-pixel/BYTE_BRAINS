"""Pydantic schemas for the Study Plan API."""

import uuid
from datetime import date
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class StudyFocus(str, Enum):
    """Allowed study plan focus options."""

    complete_syllabus = "Complete syllabus"
    improve_weak_topics = "Improve weak topics"
    balanced = "Balanced"


class PlanTaskType(str, Enum):
    """Allowed task types in a generated plan."""

    study = "study"
    practice = "practice"
    revision = "revision"
    quiz = "quiz"


class StudyPlanGenerateRequest(BaseModel):
    """Request to generate a personalized study plan."""

    subject_id: uuid.UUID
    days_available: int = Field(ge=1, le=30)
    hours_per_day: float = Field(ge=0.5, le=12)
    focus: StudyFocus = StudyFocus.balanced
    exam_date: date | None = None
    weak_topics: List[str] = Field(default_factory=list)


class StudyPlanTask(BaseModel):
    """A single task within a plan day."""

    title: str = Field(min_length=1)
    duration_minutes: int = Field(ge=1)
    type: PlanTaskType


class StudyPlanDay(BaseModel):
    """One day of the study plan."""

    day: int = Field(ge=1)
    tasks: List[StudyPlanTask] = Field(min_length=1)


class StudyPlanGenerateResponse(BaseModel):
    """Generated day-by-day study plan."""

    subject_id: uuid.UUID
    days: List[StudyPlanDay] = Field(min_length=1)
