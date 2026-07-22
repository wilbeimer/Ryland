from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid
import json
from backend.database import init_db, get_db
from backend.models import (
    CurriculumRequest,
    Course,
    Week,
    Assignment,
    Quiz,
    Submission,
    SubmissionCreate,
)
from backend.ai.curriculum import generate_curriculum
from backend.ai.grader import grade_submission
import os
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@limiter.limit("100/minute")
def root(request: Request):
    return {"message": "Hello World"}


# --- Courses ---


@app.get("/courses", response_model=list[Course])
@limiter.limit("100/minute")
def get_courses(request: Request, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses")
    rows = cur.fetchall()
    return [deserialize_course(dict(row)) for row in rows]


@app.post("/courses", response_model=dict)
@limiter.limit("10/minute")  # Lower limit for creating courses
def post_course(
    request: Request,
    course: CurriculumRequest,
    background_tasks: BackgroundTasks,
    conn=Depends(get_db),
):

    cur = conn.cursor()
    course_id = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO courses (id, name, color, status)
        VALUES (?, ?, ?, ?)
    """,
        (course_id, course.name, course.color, "pending"),
    )

    conn.commit()

    # Queue the generation to run in the background
    background_tasks.add_task(generate_curriculum, course_id, course)

    return {
        "id": course_id,
        "name": course.name,
        "color": course.color,
        "status": "pending",
    }


@app.get("/courses/{id}")
@limiter.limit("100/minute")
def get_course(request: Request, id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found")

    result = deserialize_course(dict(row))
    print(f"get_course status: {result['status']}")
    return result


@app.delete("/courses/{id}", status_code=204)
@limiter.limit("20/minute")  # Lower limit for delete operations
def delete_course(request: Request, id: str, conn=Depends(get_db)):
    cur = conn.cursor()

    # First check if the course exists
    cur.execute("SELECT id FROM courses WHERE id=?", (id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="Course not found")

    # Delete the course - cascade will handle related records
    cur.execute("DELETE FROM courses WHERE id=?", (id,))

    # Check if any rows were deleted
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Course not found")

    conn.commit()


# --- Weeks ---


@app.get("/courses/{id}/weeks", response_model=list[Week])
def get_weeks(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM course_weeks WHERE courseId=? ORDER BY week", (id,))
    rows = cur.fetchall()
    return [deserialize_week(dict(row)) for row in rows]


# --- Assignments ---


@app.get("/courses/{id}/assignments", response_model=list[Assignment])
def get_assignments(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM assignments WHERE courseId=? ORDER BY week", (id,))
    rows = cur.fetchall()
    return [deserialize_assignment(dict(row)) for row in rows]


@app.get("/assignments/{id}", response_model=Assignment)
def get_assignment(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM assignments WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return deserialize_assignment(dict(row))


# --- Quizzes ---


@app.get("/courses/{id}/quizzes")
def get_quizzes(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM quizzes WHERE courseId=? ORDER BY week", (id,))
    rows = cur.fetchall()
    return [deserialize_quiz(dict(row)) for row in rows]


@app.get("/quizzes/{id}", response_model=Quiz)
def get_quiz(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM quizzes WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return deserialize_quiz(dict(row))


# --- Submissions ---


@app.get("/assignments/{id}/submissions", response_model=list[Submission])
def get_submissions(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM submissions WHERE assignmentId=?", (id,))
    rows = cur.fetchall()
    return [dict(row) for row in rows]


@app.get("/submissions/{id}", response_model=Submission)
def get_submission(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM submissions WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return dict(row)


@app.post("/submissions", response_model=Submission)
def post_submission(
    submission: SubmissionCreate,
    background_tasks: BackgroundTasks,
    conn=Depends(get_db),
):
    cur = conn.cursor()
    submission_id = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO submissions (id, assignmentId, content, status)
        VALUES (?, ?, ?, ?)
    """,
        (submission_id, submission.assignmentId, submission.content, "pending"),
    )

    conn.commit()

    background_tasks.add_task(grade_submission, submission_id, submission)

    return {
        "id": submission_id,
        "assignmentId": submission.assignmentId,
        "content": submission.content,
        "status": "pending",
    }


# --- Deserializers ---


def deserialize_course(row: dict) -> dict:
    row["subdomains"] = json.loads(row.get("subdomains") or "[]")
    row["prerequisites"] = json.loads(row.get("prerequisites") or "[]")
    textbook = json.loads(row.get("textbook") or "null")
    row["textbook"] = textbook if textbook else None
    row["weeks"] = json.loads(row.get("weeks_data") or "[]")
    return row


def deserialize_week(row: dict) -> dict:
    row["topics"] = json.loads(row.get("topics") or "[]")
    return row


def deserialize_assignment(row: dict) -> dict:
    row["requirements"] = json.loads(row.get("requirements") or "[]")
    row["resources"] = json.loads(row.get("resources") or "[]")
    return row


def deserialize_quiz(row: dict) -> dict:
    row["questions"] = json.loads(row.get("questions") or "[]")
    return row
