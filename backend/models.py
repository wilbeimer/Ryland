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
