import json
from backend.models import RylandState, Course, CourseStatus, CurriculumRequest
from backend.ai.curriculum_agent.loop import generate_curriculum as agentic_generate
from backend.database import get_db


def generate_curriculum(course_id: str, request: CurriculumRequest) -> None:
    """
    Background task: generate a complete curriculum for a course.

    Args:
        course_id: UUID of the course row (already created in DB)
        request: CurriculumRequest with name, color, description
    """
    conn = next(get_db())  # Get a fresh DB connection for this background task

    try:
        # 1. Build initial state with empty course
        initial_course = Course(
            id=course_id,
            name=request.name,
            color=request.color,
            status=CourseStatus.PENDING,
        )
        state = RylandState(request=request, course=initial_course)

        # 2. Run the agentic loop
        final_state = agentic_generate(state)

        # 3. Persist the result
        _persist_course_to_db(conn, final_state)

    except Exception as e:
        # Mark course as failed
        cur = conn.cursor()
        cur.execute(
            "UPDATE courses SET status = ? WHERE id = ?",
            (CourseStatus.FAILED, course_id),
        )
        conn.commit()
        print(f"[ERROR] Course {course_id} generation failed: {e}")
        raise
    finally:
        conn.close()


def _persist_course_to_db(conn, state: RylandState) -> None:
    """Write the completed RylandState back to the database."""
    cur = conn.cursor()
    course = state.course

    # 1. Update course metadata
    cur.execute(
        """
        UPDATE courses
        SET description = ?, domain = ?, subdomains = ?, prerequisites = ?,
            duration_weeks = ?, hours_per_week = ?, textbook = ?, status = ?
        WHERE id = ?
        """,
        (
            course.description,
            course.domain,
            json.dumps(course.subdomains),
            json.dumps(course.prerequisites),
            course.duration_weeks,
            course.hours_per_week,
            json.dumps(course.textbook.model_dump()) if course.textbook else None,
            CourseStatus.COMPLETE if not state.errors else CourseStatus.FAILED,
            course.id,
        ),
    )

    # 2. Insert weeks
    for week in course.weeks:
        cur.execute(
            """
            INSERT INTO course_weeks (id, courseId, week, goal, topics)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                week.id,
                course.id,
                week.number,
                week.goal,
                json.dumps(week.topics),
            ),
        )

        # 3. Insert assignments for this week
        for assignment in week.assignments:
            cur.execute(
                """
                INSERT INTO assignments
                (id, courseId, week, title, type, description, requirements, resources, dueDate, points, rubric)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assignment.id,
                    course.id,
                    week.number,
                    assignment.title,
                    assignment.type.value,
                    assignment.description,
                    json.dumps(assignment.requirements),
                    json.dumps([r.model_dump() for r in assignment.resources]),
                    assignment.dueDate,
                    assignment.points,
                    assignment.rubric,
                ),
            )

        # 4. Insert quiz for this week (if it exists)
        if week.quiz:
            cur.execute(
                """
                INSERT INTO quizzes (id, courseId, week, title, type, questions, dueDate, points)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    week.quiz.id,
                    course.id,
                    week.number,
                    week.quiz.title,
                    week.quiz.type.value,
                    json.dumps([q.model_dump() for q in week.quiz.questions]),
                    week.quiz.dueDate,
                    week.quiz.points,
                ),
            )

    conn.commit()
