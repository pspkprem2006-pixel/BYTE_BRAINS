"""Pydantic schemas for the Quiz API."""

import uuid
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class QuizQuestion(BaseModel):
    """A single generated quiz question."""

    question: str = Field(min_length=1)
    options: List[str] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=1)
    topic: str = Field(min_length=1)


class QuizGenerateRequest(BaseModel):
    """Request to generate a quiz from material."""

    material_id: uuid.UUID
    question_count: int = Field(ge=5, le=10)


class QuizGenerateResponse(BaseModel):
    """Response containing generated quiz questions."""

    material_id: uuid.UUID
    questions: List[QuizQuestion]
    question_count: int