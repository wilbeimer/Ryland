from contextlib import asynccontextmanager
import logging
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import Depends, FastAPI, HTTPException

from backend.auth import get_current_user
from backend.db import DuplicateWeekError, InvalidAssignmentError, InvalidCourseError, InvalidWeekError, add_assignment_to_db, add_course_to_db, add_week_to_db, get_assignments, get_courses, get_weeks, init_db
from backend.models import Assignment, RequestAddAssignment, RequestAddWeek, Course, RequestAddCourse, User, Week


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)


# COURSES
@app.get("/courses")
def list_courses(user: Annotated[User, Depends(get_current_user)]):
    return get_courses(str(user.id))


@app.post("/courses", status_code=201)
def add_course(user: Annotated[User, Depends(get_current_user)], course: RequestAddCourse):
    course_id = uuid4()
    valid_course = Course(
        id=course_id,
        user_id=user.id,
        name=course.name,
        desc=course.desc
    )

    try:
        course_id = add_course_to_db(course=valid_course)
    except InvalidCourseError:
        logger.exception("Constraint violation creating course")
        raise HTTPException(status_code=422, detail="Invalid course data")
    return {"id": course_id}


# WEEKS
@app.get("/courses/{course_id}/weeks")
def list_weeks(user: Annotated[User, Depends(get_current_user)], course_id: UUID):
    return get_weeks(course_id=course_id)


@app.post("/courses/{course_id}/weeks")
def add_week(user: Annotated[User, Depends(get_current_user)], course_id: UUID, week: RequestAddWeek):
    week_id = uuid4()
    valid_week = Week(
        id=week_id,
        course_id=course_id,
        week_number=week.week_number,
        desc=week.desc
    )
    try:
        week_id = add_week_to_db(week=valid_week)
    except DuplicateWeekError:
        logger.exception("Duplicate week constrain violation creating week")
        raise HTTPException(status_code=409, detail="Week already exists")
    except InvalidWeekError:
        logger.exception("Constraint violation creating week")
        raise HTTPException(status_code=422, detail="Invalid week data")
    return {"id": week_id}


# ASSIGNMENTS
@app.get("/courses/{course_id}/weeks/{week_id}/assignments")
def list_assignments(user: Annotated[User, Depends(get_current_user)], course_id: UUID, week_id: UUID):
    return get_assignments(course_id=course_id, week_id=week_id)


@app.post("/courses/{course_id}/weeks/{week_id}/assignments")
def add_assignment(user: Annotated[User, Depends(get_current_user)], course_id: UUID, week_id: UUID, assignment: RequestAddAssignment):
    assignment_id = uuid4()
    valid_assignment = Assignment(
        id=assignment_id,
        week_id=week_id,
        type=assignment.type,
        name=assignment.name,
        desc=assignment.desc,
        rubric=assignment.rubric,
        due_date=assignment.due_date
    )
    try:
        assignment_id = add_assignment_to_db(assignment=valid_assignment)
    except InvalidAssignmentError:
        logger.exception("Constraint violation creating assignment")
        raise HTTPException(status_code=422, detail="Invalid assignment data")
