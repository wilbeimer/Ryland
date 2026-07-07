---
name: generate_quizzes
version: 0.1
depends_on: 
    - 02_course_resources
    - 03_course_length
    - 04_weekly_goal
    - 05_assignments
---

## Process
For each week defined in `03_course_length`, generate one quiz that tests the student's understanding of that week's material, based on:
- the resources listed in `02_course_resources` for that week
- the learning goal for that week from `04_weekly_goal`
- the assignments already created in `05_assignments`, to avoid duplicating questions

Each quiz should include a mix of question types (e.g. multiple choice, short answer) sufficient to cover the week's key concepts.

## Output
Return as JSON:
{
    "quizzes": [
        {
            "week": 1,
            "title": "...",
            "questions": [
                {
                    "type": "multiple_choice",
                    "question": "...",
                    "options": ["...", "...", "...", "..."],
                    "answer": "..."
                },
                {
                    "type": "short_answer",
                    "question": "...",
                    "answer": "..."
                }
            ]
        }
    ]
