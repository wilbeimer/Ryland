import os
import sqlite3
from backend.ai.runner import run_stage
from backend.models import Course, CourseStatus, CurriculumRequest, RylandState

STAGES_DIR = os.path.join(os.path.dirname(__file__), "curriculum", "stages")


def save_course_status(course: Course):
    with sqlite3.connect("curriculum.db", check_same_thread=False, timeout=30) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "UPDATE courses SET status = ? WHERE id = ?",
            (course.status.value, course.id),
        )
        conn.commit()


def get_stages():
    """Return stage folder names in order."""
    stages = sorted(
        [
            d
            for d in os.listdir(STAGES_DIR)
            if os.path.isdir(os.path.join(STAGES_DIR, d))
        ]
    )
    return stages


def generate_curriculum(course_id: str, request: CurriculumRequest):
    state = RylandState(
        request=request,
        course=Course(
            id=course_id,
            name=request.name,
            color=request.color,
            description=request.description,
        ),
    )

    try:
        state.course.status = CourseStatus.GENERATING
        save_course_status(state.course)

        print("BEFORE")
        print(state.model_dump_json(indent=2))

        SKIP_STAGES = {
            "06_assigment_description",
            "08_assignment_resources",
            # add any unfinished stages here
        }

        for stage in get_stages():
            if stage in SKIP_STAGES:
                continue

            print(f"\n=== {stage} ===")
            run_stage(stage, state)

        state.course.status = CourseStatus.COMPLETE
        save_course_status(state.course)

        print("AFTER")
        print(state.model_dump_json(indent=2))

    except Exception:
        import traceback

        traceback.print_exc()

        state.course.status = CourseStatus.FAILED
        save_course_status(state.course)

        raise
