from datetime import datetime, timedelta
from enum import Enum
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, SecretStr, field_validator


class AssignmentType(Enum):
    TEXT = "text"
    QUIZ = "quiz"


class QuestionType(Enum):
    SHORT = 'short answer'
    MULTI = 'multiple choice'


class User(BaseModel):
    id: UUID
    email: str
    password: SecretStr


class Course(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str


class RequestAddCourse(BaseModel):
    name: str
    description: str


class CourseOut(BaseModel):
    id: UUID
    name: str
    description: str


class Week(BaseModel):
    id: UUID
    course_id: UUID
    week_number: int
    description: str


class RequestAddWeek(BaseModel):
    week_number: int
    description: str


class WeekOut(BaseModel):
    id: UUID
    week_number: int
    description: str


class Assignment(BaseModel):
    id: UUID
    week_id: UUID
    type: AssignmentType
    name: str
    description: str
    rubric: dict
    due_date: datetime


class RequestAddAssignment(BaseModel):
    type: AssignmentType
    name: str
    description: str
    rubric: dict
    due_date: datetime


class AssignmentOut(BaseModel):
    id: UUID
    type: AssignmentType
    name: str
    description: str
    rubric: dict
    due_date: datetime


class Submission(BaseModel):
    id: UUID
    assignment_id: UUID
    submission_time: datetime
    content: Optional[dict] = None
    grade: Optional[float] = None


class QuizQuestion(BaseModel):
    question_type: QuestionType
    prompt: str
    options: list[str] | None = None
    correct_answer: str


class QuizQuestionOut(BaseModel):
    question_type: QuestionType
    prompt: str
    options: list[str] | None = None


class Quiz(BaseModel):
    id: UUID
    assignment_id: UUID
    time_limit: timedelta
    questions: list[QuizQuestion]


class RequestAddQuiz(BaseModel):
    time_limit: timedelta
    questions: list[QuizQuestion]


class PrivateQuizOut(BaseModel):
    id: UUID
    time_limit: timedelta
    questions: list[QuizQuestion]


class PublicQuizOut(BaseModel):
    id: UUID
    time_limit: timedelta
    questions: list[QuizQuestionOut]


class GenerateCourseRequest(BaseModel):
    goal: str = Field(min_length=1, description="What the learner wants to learn")
    level: str = Field(min_length=1, description="Current level, in the learner's own words")
    time_available: str = Field(
        min_length=1,
        description="How much time they can spend, including pace and duration",
    )
    timezone: str = Field(
        min_length=1,
        description="IANA timezone name used for due dates, for example America/New_York",
    )

    @field_validator("goal", "level", "time_available", "timezone")
    @classmethod
    def strip_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class GenerateJobOut(BaseModel):
    job_id: UUID
    status: Literal["pending", "running", "succeeded", "failed"]
    detail: str | None = None
    course_id: UUID | None = None
    course: CourseOut | None = None
    error: str | None = None
