from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
from backend.database import init_db, get_db
from backend.models import CourseCreate, Course, Assignment, AssignmentCreate, Submission, SubmissionCreate
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


# Courses
@app.get("/courses", response_model=list[Course])
def get_courses(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses")
    rows = cur.fetchall()
    return [dict(row) for row in rows]


@app.post("/courses", response_model=Course)
def post_course(course: CourseCreate, conn=Depends(get_db)):
    cur = conn.cursor()
    course_id = str(uuid.uuid4())
    cur.execute("INSERT INTO courses (id, name, description, color) VALUES (?, ?, ?, ?)", (course_id, course.name, course.description, course.color))
    conn.commit()
    return {"id": course_id, **course.model_dump()}


@app.get("/courses/{id}", response_model=Course)
def get_course(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return dict(row)


@app.delete("/courses/{id}", status_code=204)
def delete_course(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("DELETE FROM courses WHERE id=?", (id,))
    conn.commit()


# Assignments
@app.get("/courses/{id}/assignments", response_model=list[Assignment])
def get_assignments(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM assignments WHERE courseId=?", (id,))
    rows = cur.fetchall()
    return [dict(row) for row in rows]


@app.post("/assignments", response_model=Assignment)
def post_assignment(assignment: AssignmentCreate, conn=Depends(get_db)):
    cur = conn.cursor()
    assignment_id = str(uuid.uuid4())
    cur.execute("INSERT INTO assignments (id, courseId, title, type, dueDate, points, content, rubric) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (assignment_id, assignment.courseId, assignment.title, assignment.type, assignment.dueDate, assignment.points, assignment.content, assignment.rubric))
    conn.commit()
    return {"id": assignment_id, **assignment.model_dump()}


@app.get("/assignments/{id}", response_model=Assignment)
def get_assignment(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM assignments WHERE id=?", (id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return dict(row)


# Submissions
@app.get("/assignments/{id}/submissions", response_model=list[Submission])
def get_submissions(id: str, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM submissions WHERE assignmentId=?", (id,))
    rows = cur.fetchall()
    return [dict(row) for row in rows]


@app.post("/submissions", response_model=Submission)
def post_submission(submission: SubmissionCreate, conn=Depends(get_db)):
    cur = conn.cursor()
    submission_id = str(uuid.uuid4())
    cur.execute("INSERT INTO submissions (id, assignmentId, grade, feedback, content) VALUES (?, ?, ?, ?, ?)", (submission_id, submission.assignmentId, submission.grade, submission.feedback, submission.content))
    conn.commit()
    return {"id": submission_id, **submission.model_dump()}


@app.patch("/submissions")
def patch_submission():
    pass
