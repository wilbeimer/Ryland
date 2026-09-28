from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, SecretStr


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
    desc: str


class RequestAddCourse(BaseModel):
    name: str
    desc: str


class Week(BaseModel):
    id: UUID
    course_id: UUID
    week_number: int
    desc: str


class RequestAddWeek(BaseModel):
    week_number: int
    desc: str


class Assignment(BaseModel):
    id: UUID
    week_id: UUID
    type: AssignmentType
    name: str
    desc: str
    rubric: dict
    due_date: datetime


class Submission(BaseModel):
    id: UUID
    assignment_id: UUID
    submission_time: datetime
    content: Optional[dict] = None
    grade: float


class Quiz(BaseModel):
    id: UUID
    assignment_id: UUID
    time_limit: timedelta


class Question(BaseModel):
    id: UUID
    quiz_id: UUID
    type: QuestionType
    desc: str
    correct: dict
