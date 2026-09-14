from pydantic import BaseModel


class Course(BaseModel):
    name: str
    desc: str
