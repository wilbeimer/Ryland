from pydantic import BaseModel, field_validator, Field
from enum import Enum


class CourseStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"


class QuestionType(str, Enum):
    MULTIPLE = "multiple_choice"
    SHORT = "short_answer"


class AssignmentType(str, Enum):
    WRITTEN = "written"
    CHECKLIST = "checklist"
    PROJECT = "project"
    PRESENTATION = "presentation"


class QuizType(str, Enum):
    WEEKLY = "weekly"
    MIDTERM = "midterm"
    FINAL = "final"
    REVIEW = "review"


class ResourceSource(str, Enum):
    TEXTBOOK = "textbook"
    YOUTUBE = "youtube"
    WEB = "web"
    ARTICLE = "article"


class CurriculumRequest(BaseModel):
    name: str
    color: str
    description: str = ""


class Resource(BaseModel):
    title: str
    url: str
    source: ResourceSource = ResourceSource.ARTICLE


class Question(BaseModel):
    type: QuestionType
    prompt: str
    choices: list[str] = Field(default_factory=list)
    answer: str


class Assignment(BaseModel):
    id: str

    title: str
    type: AssignmentType = AssignmentType.WRITTEN

    description: str = ""

    requirements: list[str] = Field(default_factory=list)
    resources: list[Resource] = Field(default_factory=list)

    dueDate: str = ""
    points: float = 100
    rubric: str = ""

    @field_validator("points", mode="before")
    @classmethod
    def default_points(cls, v):
        return v if v is not None else 100

    @field_validator("dueDate", "rubric", "description", mode="before")
    @classmethod
    def default_str(cls, v):
        return v if v is not None else ""


class Quiz(BaseModel):
    id: str

    title: str
    type: QuizType = QuizType.WEEKLY

    questions: list[Question] = Field(default_factory=list)

    dueDate: str = ""
    points: float = 100

    @field_validator("points", mode="before")
    @classmethod
    def default_points(cls, v):
        return v if v is not None else 100

    @field_validator("dueDate", mode="before")
    @classmethod
    def default_str(cls, v):
        return v if v is not None else ""


class Week(BaseModel):
    id: str
    number: int

    goal: str
    topics: list[str]

    assignments: list[Assignment] = Field(default_factory=list)
    quiz: Quiz | None = None


class Textbook(BaseModel):
    title: str
    authors: list[str]
    edition: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    link: str | None = None


class Course(BaseModel):
    id: str
    name: str

    color: str
    status: CourseStatus = CourseStatus.PENDING

    description: str | None = None
    domain: str | None = None
    subdomains: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)

    duration_weeks: int | None = None
    hours_per_week: int | None = None
    weeks: list[Week] = Field(default_factory=list)
    textbook: Textbook | None = None

    @property
    def week_count(self) -> int:
        return len(self.weeks)


class Submission(BaseModel):
    id: str
    assignmentId: str
    grade: float | None = None
    feedback: str | None = None
    content: str
    status: str = "pending"


class SubmissionCreate(BaseModel):
    assignmentId: str
    content: str


class RylandState(BaseModel):
    request: CurriculumRequest
    course: Course

    current_stage: str | None = None
    errors: list[str] = Field(default_factory=list)
