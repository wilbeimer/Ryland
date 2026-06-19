from pydantic import BaseModel


class CourseCreate(BaseModel):
    name: str
    description: str
    color: str


class Course(BaseModel):
    id: str
    name: str
    description: str
    color: str


class Assignment(BaseModel):
    id: str
    courseId: str
    title: str
    type: str
    dueDate: str = ''
    points: float = 100
    content: str = ''
    rubric: str = ''


class AssignmentCreate(BaseModel):
    courseId: str
    title: str
    type: str
    dueDate: str = ''
    points: float = 100
    content: str = ''
    rubric: str = ''


class Submission(BaseModel):
    id: str
    assignmentId: str
    grade: float = 0
    feedback: str = ''
    content: str


class SubmissionCreate(BaseModel):
    assignmentId: str
    grade: float = 0
    feedback: str = ''
    content: str
