from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException

from backend.db import InvalidCourseError, create_course, get_courses, init_db
from backend.models import Course


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)


@app.get("/courses")
def list_courses():
    return get_courses()


@app.post("/courses", status_code=201)
def add_course(course: Course):
    try:
        course_id = create_course(course=course)
    except InvalidCourseError:
        logger.exception("Constraint violation creating course")
        raise HTTPException(status_code=422, detail="Invalid course data")
    return {"id": course_id}
