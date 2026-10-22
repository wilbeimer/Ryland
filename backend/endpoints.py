from contextlib import asynccontextmanager
from dataclasses import dataclass, replace
import logging
import os
import threading
from typing import Annotated
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from agent.agent_loop import run_generation
from backend.auth import get_current_user
from backend.db import add_assignment_to_db, add_course_to_db, add_quiz_to_db, add_week_to_db, get_assignments, get_courses, get_owned_assignment, get_owned_course, get_owned_week, get_quiz, get_weeks, init_db
from backend.models import Assignment, AssignmentOut, CourseOut, GenerateCourseRequest, GenerateJobOut, PublicQuizOut, Quiz, RequestAddAssignment, RequestAddQuiz, RequestAddWeek, Course, RequestAddCourse, User, Week, WeekOut
from backend.exceptions import DuplicateWeekError, InvalidAssignmentError, InvalidCourseError, InvalidQuizError, InvalidWeekError


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


load_dotenv()

app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)

_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def allowed_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS")
    if raw is None or not raw.strip():
        raw = _DEFAULT_CORS_ORIGINS
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class GenerationJob:
    job_id: UUID
    user_id: UUID
    status: str
    detail: str | None = None
    course_id: UUID | None = None
    error: str | None = None


# One uvicorn process. A local page polls these; a restart drops them.
_jobs: dict[UUID, GenerationJob] = {}
_jobs_lock = threading.Lock()


def _update_job(job_id: UUID, **fields) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        for key, value in fields.items():
            setattr(job, key, value)


def _snapshot_job(job_id: UUID) -> GenerationJob | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return None
        return replace(job)


def _job_response(job: GenerationJob) -> GenerateJobOut:
    course = None
    if job.course_id is not None:
        for row in get_courses(job.user_id):
            if str(row["id"]) == str(job.course_id):
                course = CourseOut.model_validate(row)
                break
    return GenerateJobOut(
        job_id=job.job_id,
        status=job.status,
        detail=job.detail,
        course_id=job.course_id,
        course=course,
        error=job.error,
    )


def _run_generation_job(job_id: UUID, user_id: UUID, body: GenerateCourseRequest) -> None:
    def on_progress(message: str) -> None:
        _update_job(job_id, status="running", detail=message)

    try:
        _update_job(job_id, status="running", detail="Starting course generation")
        result = run_generation(
            user_id=user_id,
            goal=body.goal,
            level=body.level,
            time_available=body.time_available,
            timezone_name=body.timezone,
            on_progress=on_progress,
        )
        if result.course_id:
            detail = (result.summary or "Course created")[:2000]
            _update_job(
                job_id,
                status="succeeded",
                course_id=UUID(str(result.course_id)),
                detail=detail,
                error=None,
            )
            return

        if result.completed:
            error = "The agent finished without creating a course"
        else:
            error = "Generation hit the turn limit before creating a course"
        _update_job(job_id, status="failed", error=error, detail=result.summary or None)
    except Exception as exc:
        logger.exception("Course generation failed for job %s", job_id)
        _update_job(job_id, status="failed", error=(str(exc) or "Course generation failed")[:500])


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


@app.post("/courses/generate", status_code=202, response_model=GenerateJobOut)
def start_course_generation(
    user: Annotated[User, Depends(get_current_user)],
    body: GenerateCourseRequest,
    response: Response,
):
    job = GenerationJob(job_id=uuid4(), user_id=user.id, status="pending", detail="Queued")
    with _jobs_lock:
        _jobs[job.job_id] = job
    snapshot = replace(job)
    response.headers["Location"] = f"/courses/generate/{job.job_id}"
    threading.Thread(
        target=_run_generation_job,
        args=(job.job_id, user.id, body),
        name=f"generate-{job.job_id}",
        daemon=True,
    ).start()
    return _job_response(snapshot)


@app.get("/courses/generate/{job_id}", response_model=GenerateJobOut)
def get_course_generation(
    user: Annotated[User, Depends(get_current_user)],
    job_id: UUID,
):
    job = _snapshot_job(job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return _job_response(job)


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


@app.post("/assignments/{assignment_id}/quiz", status_code=201)
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
