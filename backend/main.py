from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
from backend.database import init_db, get_db
from backend.models import CourseCreate, Course
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


@app.get("/courses", response_model=list[Course])
def get_courses(conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses")
    rows = cur.fetchall()
    return [dict(row) for row in rows]


@app.post("/courses", response_model=Course)
def post_courses(course: CourseCreate, conn=Depends(get_db)):
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
