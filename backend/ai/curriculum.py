import json
import os
import sqlite3
import uuid
from backend.ai.runner import run_stage
from backend.ai.youtube import search_youtube
from backend.models import CourseCreate

STAGES_DIR = os.path.join(os.path.dirname(__file__), "curriculum", "stages")


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


def generate_curriculum(course_id: str, course: CourseCreate):
    conn = sqlite3.connect("curriculum.db", check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        stages = get_stages()
        results = {}

        SKIP_STAGES = {"08_assignment_resources"}

        # Run all stages, first stage gets course inputs
        for i, stage in enumerate(stages):
            if stage in SKIP_STAGES:
                continue
            if i == 0:
                results[stage] = run_stage(
                    stage,
                    {
                        "course_name": course.name,
                        "course_description": course.description,
                    },
                )
            else:
                results[stage] = run_stage(stage)

        # Convenience aliases
        r01 = results.get("01_course_description", {})
        r02 = results.get("02_course_resources", {})
        r03 = results.get("03_course_length", {})
        r04 = results.get("04_weekly_goal", {})
        _ = results.get("05_assignments", {})
        r06 = results.get("06_assignment_description", {})
        r08 = results.get("08_assignment_resources", {})

        # Build a lookup map for resources by assignment title
        resources_map = {}
        for item in r08.get("assignment_resources", []):
            resources_map[item["assignment_title"]] = item.get("resources", [])

        # Insert course
        cur.execute(
            """
            UPDATE courses SET
                description = ?,
                domain = ?,
                subdomains = ?,
                prerequisites = ?,
                weeks = ?,
                hours_per_week = ?,
                status = 'completed',
                textbook = ?
            WHERE id = ?
        """,
            (
                r01["description"],
                r01["domain"],
                json.dumps(r01["subdomains"]),
                json.dumps(r01["prerequisites"]),
                r03["weeks"],
                r03["hours_per_week"],
                json.dumps(r02.get("textbook", {})),
                course_id,
            ),
        )

        if cur.rowcount == 0:
            raise RuntimeError(
                f"Course update matched 0 rows for id={course_id} — check parameter order"
            )

        # Insert weeks
        week_id_map = {}
        for week in r04["weekly_goals"]:
            week_id = str(uuid.uuid4())
            week_id_map[week["week"]] = week_id
            cur.execute(
                """
                INSERT INTO course_weeks (id, courseId, week, goal, topics)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    week_id,
                    course_id,
                    week["week"],
                    week["goal"],
                    json.dumps(week["topics"]),
                ),
            )

        print(f"course rows affected: {cur.rowcount}")

        # Insert assignments
        print("Starting Youtube resource fetch...")
        for assignment in r06["assignments"]:
            print(f"Fetching YouTube for: {assignment['title']}")

            query = f"{assignment['title']} {r01['domain']} tutorials"
            try:
                videos = search_youtube(query, max_results=2)
            except Exception as e:
                print(f"YouTube search failed for {assignment['title']}: {e}")
                videos = []

            print("YouTube fetch complete, saving to db...")

            cur.execute(
                """
                INSERT INTO assignments (id, courseId, weekId, week, title, type, description, requirements, resources)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(uuid.uuid4()),
                    course_id,
                    week_id_map.get(assignment["week"], ""),
                    assignment["week"],
                    assignment["title"],
                    assignment["type"],
                    assignment["description"],
                    json.dumps(assignment["requirements"]),
                    json.dumps(videos),
                ),
            )

            print(f"assignment rows affected: {cur.rowcount}")

        print("committing course")

        conn.commit()
    except Exception as e:
        import traceback

        traceback.print_exc()
        conn.rollback()
        cur.execute("UPDATE courses SET status = 'failed' WHERE id = ?", (course_id,))
        conn.commit()
        print(f"Pipeline failed for course {course_id}: {e}")
    finally:
        conn.close()

        print("connection closed")
