from pydantic import BaseModel, field_validator


class CourseCreate(BaseModel):
    name: str
    color: str
    description: str = ""


class Course(BaseModel):
    id: str
    name: str
    color: str
    status: str = "pending"
    description: str | None = None
    domain: str | None = None
    subdomains: list[str] = []
    prerequisites: list[str] = []
    weeks: int | None = None
    hours_per_week: int | None = None
    textbook: dict = {}


class Assignment(BaseModel):
    id: str
    courseId: str
    weekId: str = ""
    week: int = 0
    title: str
    type: str
    description: str = ""
    requirements: list[str] = []
    resources: list[dict] = []

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


class AssignmentCreate(BaseModel):
    courseId: str
    weekId: str = ""
    week: int = 0
    title: str
    type: str
    description: str = ""
    requirements: list[str] = []
    dueDate: str = ""
    points: float = 100
    rubric: str = ""
    content: str = ""

    @field_validator("points", mode="before")
    @classmethod
    def default_points(cls, v):
        return v if v is not None else 100

    @field_validator("dueDate", "rubric", "description", mode="before")
    @classmethod
    def default_str(cls, v):
        return v if v is not None else ""


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


class Week(BaseModel):
    id: str
    courseId: str
    week: int
    goal: str
    topics: list[str]


class WeekCreate(BaseModel):
    courseId: str
    week: int
    goal: str
    topics: list[str]
