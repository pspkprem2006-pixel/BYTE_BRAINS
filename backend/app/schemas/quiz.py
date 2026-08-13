"""Pydantic schemas for the Quiz API."""

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuizQuestion(BaseModel):
    """A single generated quiz question."""

    question: str = Field(min_length=1)
    options: List[str] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=1)
    topic: str = Field(min_length=1)


class QuizGenerateRequest(BaseModel):
    """Request to generate a quiz.

    Either ``material_id`` (uploaded material) or ``subject_id`` (selected
    web resources for a subject) — or both — must be provided.
    """

    material_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    question_count: int = Field(ge=5, le=10)

    @model_validator(mode="after")
    def _at_least_one_source(self) -> "QuizGenerateRequest":
        if self.material_id is None and self.subject_id is None:
            raise ValueError("material_id or subject_id is required")
        return self


class QuizGenerateResponse(BaseModel):
    """Response containing generated quiz questions."""

    material_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    questions: List[QuizQuestion]
    question_count: int


class TopicResult(BaseModel):
    """Per-topic performance inside one quiz attempt."""

    topic: str = Field(min_length=1, max_length=200)
    correct: int = Field(ge=0)
    total: int = Field(ge=1)

    @model_validator(mode="after")
    def _correct_must_fit_topic(self) -> "TopicResult":
        if self.correct > self.total:
            raise ValueError("correct cannot exceed total for a topic")
        return self


class QuizSubmitRequest(BaseModel):
    """Request to persist a finished quiz attempt.

    The score percentage is derived server-side from correct_answers and
    total_questions so the stored value always matches the answers.

    Either ``material_id`` or ``subject_id`` must be provided; the subject
    is resolved from the material when only the material is given.
    """

    material_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    total_questions: int = Field(ge=1)
    correct_answers: int = Field(ge=0)
    topic_results: List[TopicResult] = []

    @model_validator(mode="after")
    def _at_least_one_source(self) -> "QuizSubmitRequest":
        if self.material_id is None and self.subject_id is None:
            raise ValueError("material_id or subject_id is required")
        return self

    @model_validator(mode="after")
    def _answers_must_fit_quiz(self) -> "QuizSubmitRequest":
        if self.correct_answers > self.total_questions:
            raise ValueError(
                "correct_answers cannot exceed total_questions"
            )
        return self

    @model_validator(mode="after")
    def _topics_must_be_unique(self) -> "QuizSubmitRequest":
        names = [result.topic for result in self.topic_results]
        if len(names) != len(set(names)):
            raise ValueError("topic_results cannot contain duplicate topics")
        return self


class QuizSubmitResponse(BaseModel):
    """Confirmation of a persisted quiz attempt."""

    attempt_id: uuid.UUID
    quiz_title: str
    total_questions: int
    correct_answers: int
    score: int
    completed_at: datetime


class QuizAttemptSummary(BaseModel):
    """One persisted quiz attempt, for history/dashboard display."""

    id: uuid.UUID
    quiz_title: str
    subject_id: uuid.UUID
    subject_name: str
    total_questions: int
    correct_answers: int
    score: int
    completed_at: datetime | None