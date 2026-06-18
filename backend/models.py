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
