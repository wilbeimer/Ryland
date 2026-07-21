import json
from pathlib import Path
import sqlite3
from ai.runner import run_stage
from models import SubmissionCreate

GRADING_STAGES_DIR = Path(__file__).parent / "grading" / "stages"


def grade_submission(submission_id: str, submission: SubmissionCreate):
    conn = sqlite3.connect("curriculum.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        # Fetch the assignment
        cur.execute("SELECT * FROM assignments WHERE id=?", (submission.assignmentId,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Assignment {submission.assignmentId} not found")
        assignment = dict(row)
        assignment["requirements"] = json.loads(assignment.get("requirements") or "[]")

        _ = run_stage(
            "01_analyze",
            {
                "submission_content": submission.content,
                "assignment_title": assignment["title"],
                "assignment_description": assignment["description"],
                "requirements": json.dumps(assignment["requirements"]),
            },
            stages_dir=GRADING_STAGES_DIR,
        )

        result_02 = run_stage("02_score", stages_dir=GRADING_STAGES_DIR)
        result_03 = run_stage("03_feedback", stages_dir=GRADING_STAGES_DIR)

        grade = result_02["grade"]
        feedback = result_03["feedback"]

        # Update submission
        cur.execute(
            """
            UPDATE submissions SET grade=?, feedback=?, status='completed'
            WHERE id=?
        """,
            (grade, feedback, submission_id),
        )
        conn.commit()

    except Exception as e:
        cur.execute(
            "UPDATE submissions SET status='failed' WHERE id=?", (submission_id,)
        )
        conn.commit()
        print(f"Grading failed for submission {submission_id}: {e}")
    finally:
        conn.close()
