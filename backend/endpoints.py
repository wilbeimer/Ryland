from contextlib import asynccontextmanager
import logging
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import Depends, FastAPI, HTTPException

from backend.auth import get_current_user
from backend.db import add_assignment_to_db, add_course_to_db, add_quiz_to_db, add_week_to_db, get_assignments, get_courses, get_owned_assignment, get_owned_course, get_owned_week, get_quiz, get_weeks, init_db
from backend.models import Assignment, AssignmentOut, CourseOut, PublicQuizOut, Quiz, RequestAddAssignment, RequestAddQuiz, RequestAddWeek, Course, RequestAddCourse, User, Week, WeekOut
from backend.exceptions import DuplicateWeekError, InvalidAssignmentError, InvalidCourseError, InvalidQuizError, InvalidWeekError


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)


# COURSES
@app.get("/courses", response_model=list[CourseOut])
def list_courses(user: Annotated[User, Depends(get_current_user)]):
    return get_courses(user.id)


@app.post("/courses", status_code=201)
def add_course(user: Annotated[User, Depends(get_current_user)], course: RequestAddCourse):
    course_id = uuid4()
    valid_course = Course(
        **course.model_dump(),
        id=course_id,
        user_id=user.id,
    )

    try:
        course_id = add_course_to_db(course=valid_course)
    except InvalidCourseError:
        logger.exception("Constraint violation creating course")
        raise HTTPException(status_code=422, detail="Invalid course data")
    return {"id": course_id}


# WEEKS
@app.get("/courses/{course_id}/weeks", response_model=list[WeekOut])
def list_weeks(user: Annotated[User, Depends(get_current_user)], course_id: UUID):
    if not get_owned_course(course_id, user.id):
        raise HTTPException(401, "Access denied to course")
    return get_weeks(course_id=course_id)


@app.post("/courses/{course_id}/weeks", status_code=201)
def add_week(user: Annotated[User, Depends(get_current_user)], course_id: UUID, week: RequestAddWeek):
    if not get_owned_course(course_id=course_id, user_id=user.id):
        raise HTTPException(401, "Access denied to course")
    week_id = uuid4()
    valid_week = Week(
        **week.model_dump(),
        id=week_id,
        course_id=course_id,
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
@app.get("/weeks/{week_id}/assignments", response_model=list[AssignmentOut])
def list_assignments(user: Annotated[User, Depends(get_current_user)], week_id: UUID):
    if not get_owned_week(week_id=week_id, user_id=user.id):
        raise HTTPException(401, "Access denied to week")
    return get_assignments(week_id=week_id)


@app.post("/weeks/{week_id}/assignments", status_code=201)
def add_assignment(user: Annotated[User, Depends(get_current_user)], week_id: UUID, assignment: RequestAddAssignment):
    if not get_owned_week(week_id=week_id, user_id=user.id):
        raise HTTPException(401, "Access denied to week")
    assignment_id = uuid4()
    valid_assignment = Assignment(
        **assignment.model_dump(),
        id=assignment_id,
        week_id=week_id,
    )
    try:
        assignment_id = add_assignment_to_db(assignment=valid_assignment)
    except InvalidAssignmentError:
        logger.exception("Constraint violation creating assignment")
        raise HTTPException(status_code=422, detail="Invalid assignment data")
    return {"id": assignment_id}


# QUIZZES
@app.get("/assignments/{assignment_id}/quiz", response_model=PublicQuizOut)
def list_quiz(user: Annotated[User, Depends(get_current_user)], assignment_id: UUID):
    if not get_owned_assignment(assignment_id=assignment_id, user_id=user.id):
        raise HTTPException(401, "Access denied to assignment")
    return get_quiz(assignment_id=assignment_id)


@app.post("/assignments/{assignment_id}/quiz")
def add_quiz(user: Annotated[User, Depends(get_current_user)], assignment_id: UUID, quiz: RequestAddQuiz):
    if not get_owned_assignment(assignment_id=assignment_id, user_id=user.id):
        raise HTTPException(401, "Access denied to assignment")
    quiz_id = uuid4()
    valid_quiz = Quiz(
        **quiz.model_dump(),
        id=quiz_id,
        assignment_id=assignment_id,
    )
    try:
        quiz_id = add_quiz_to_db(quiz=valid_quiz)
    except InvalidQuizError:
        logger.exception("Constraint violation creating quiz")
        raise HTTPException(status_code=422, detail="Invalid quiz data")
    return {"id": quiz_id}
