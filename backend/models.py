from datetime import date, datetime, timedelta
from enum import Enum
from re import fullmatch
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, SecretStr, field_validator

from backend.course_dates import DEFAULT_COURSE_COLOR, HEX_COLOR_PATTERN


class AssignmentType(Enum):
    TEXT = "text"
    QUIZ = "quiz"


class QuestionType(Enum):
    SHORT = "short answer"
    MULTI = "multiple choice"


class User(BaseModel):
    id: UUID
    email: str
    password: SecretStr


def _normalize_hex_color(value: str) -> str:
    stripped = value.strip()
    if not fullmatch(HEX_COLOR_PATTERN, stripped):
        raise ValueError("color must be a #RRGGBB hex string")
    return stripped.lower()


class Course(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    color: str = DEFAULT_COURSE_COLOR
    start_date: date = Field(default_factory=date.today)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        return _normalize_hex_color(value)


class RequestAddCourse(BaseModel):
    name: str
    description: str
    color: str = DEFAULT_COURSE_COLOR
    start_date: date | None = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        return _normalize_hex_color(value)


class RequestPatchCourse(BaseModel):
    color: str

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        return _normalize_hex_color(value)


class CourseOut(BaseModel):
    id: UUID
    name: str
    description: str
    color: str
    start_date: date


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
    start_date: date
    end_date: date


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
    due_date: datetime | None = None


class AssignmentOut(BaseModel):
    id: UUID
    type: AssignmentType
    name: str
    description: str
    rubric: dict
    due_date: datetime


class CalendarAssignmentOut(BaseModel):
    id: UUID
    type: AssignmentType
    name: str
    description: str
    rubric: dict
    due_date: datetime
    course_id: UUID
    course_name: str
    course_color: str


class CalendarWeekOut(BaseModel):
    start_date: date
    end_date: date
    assignments: list[CalendarAssignmentOut]


class Submission(BaseModel):
    id: UUID
    assignment_id: UUID
    submission_time: datetime
    content: dict | None = None
    grade: float | None = None


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
    level: str = Field(
        min_length=1, description="Current level, in the learner's own words"
    )
    time_available: str = Field(
        min_length=1,
        description="How much time they can spend, including pace and duration",
    )
    timezone: str = Field(
        min_length=1,
        description="IANA timezone name used for due dates, for example America/New_York",
    )

    @field_validator("goal", "level", "time_available")
    @classmethod
    def strip_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("timezone")
    @classmethod
    def require_iana_timezone(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        try:
            ZoneInfo(stripped)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(
                "must be an IANA timezone name, for example America/New_York"
            ) from exc
        return stripped


class GenerateAnswersRequest(BaseModel):
    answers: list[str] = Field(
        min_length=1,
        max_length=20,
        description="Answers aligned 1:1 with the pending clarifying questions",
    )

    @field_validator("answers")
    @classmethod
    def strip_and_require_answers(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            stripped = item.strip() if isinstance(item, str) else ""
            if not stripped:
                raise ValueError("answers must not be blank")
            if len(stripped) > 2000:
                raise ValueError("each answer must be at most 2000 characters")
            cleaned.append(stripped)
        return cleaned


class GenerateJobOut(BaseModel):
    job_id: UUID
    status: Literal[
        "pending",
        "running",
        "awaiting_input",
        "succeeded",
        "incomplete",
        "failed",
    ]
    detail: str | None = None
    course_id: UUID | None = None
    course: CourseOut | None = None
    error: str | None = None
    questions: list[str] | None = None
