from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
from backend.database import init_db, get_db
from backend.models import (
    CourseCreate,
    Course,
    Week,
    WeekCreate,
    Assignment,
    AssignmentCreate,
    Submission,
    SubmissionCreate,
)
from backend.ai.curriculum import generate_curriculum
from backend.ai.grader import grade_submission
import os

app = FastAPI()
init_db()

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello World"}


# --- Courses ---


@app.get("/courses", response_model=list[Course])
def get_courses(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses")
    rows = cur.fetchall()
    return [deserialize_course(dict(row)) for row in rows]


@app.post("/courses", response_model=dict)
def post_course(
    course: CourseCreate, background_tasks: BackgroundTasks, conn=Depends(get_db)
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


@app.get("/courses/{id}", response_model=Course)
def get_course(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found")

    result = deserialize_course(dict(row))
    print(f"get_course status: {result['status']}")
    return result


@app.delete("/courses/{id}", status_code=204)
def delete_course(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("DELETE FROM courses WHERE id=?", (id,))
    conn.commit()


# --- Weeks ---


@app.get("/courses/{id}/weeks", response_model=list[Week])
def get_weeks(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM course_weeks WHERE courseId=? ORDER BY week", (id,))
    rows = cur.fetchall()
    return [deserialize_week(dict(row)) for row in rows]


@app.post("/weeks", response_model=Week)
def post_week(week: WeekCreate, conn=Depends(get_db)):
    cur = conn.cursor()
    week_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO course_weeks (id, courseId, week, goal, topics)
        VALUES (?, ?, ?, ?, ?)
    """,
        (week_id, week.courseId, week.week, week.goal, json.dumps(week.topics)),
    )
    conn.commit()
    return {"id": week_id, **week.model_dump()}


# --- Assignments ---


@app.get("/courses/{id}/assignments", response_model=list[Assignment])
def get_assignments(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM assignments WHERE courseId=? ORDER BY week", (id,))
    rows = cur.fetchall()
    return [deserialize_assignment(dict(row)) for row in rows]


@app.post("/assignments", response_model=Assignment)
def post_assignment(assignment: AssignmentCreate, conn=Depends(get_db)):
    cur = conn.cursor()
    assignment_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO assignments (id, courseId, weekId, week, title, type, description, requirements, dueDate, points, content, rubric)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            assignment_id,
            assignment.courseId,
            assignment.weekId,
            assignment.week,
            assignment.title,
            assignment.type,
            assignment.description,
            json.dumps(assignment.requirements),
            assignment.dueDate,
            assignment.points,
            assignment.content,
            assignment.rubric,
        ),
    )
    conn.commit()
    return {"id": assignment_id, **assignment.model_dump()}


@app.get("/assignments/{id}", response_model=Assignment)
def get_assignment(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM assignments WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return deserialize_assignment(dict(row))


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
    row["textbook"] = json.loads(row.get("textbook") or "{}")
    return row


def deserialize_week(row: dict) -> dict:
    row["topics"] = json.loads(row.get("topics") or "[]")
    return row


def deserialize_assignment(row: dict) -> dict:
    row["requirements"] = json.loads(row.get("requirements") or "[]")
    row["resources"] = json.loads(row.get("resources") or "[]")
    return row
