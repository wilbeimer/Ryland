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

Create one quiz for every week in the course.

Each quiz should assess that week's learning goal and topics while avoiding questions that simply duplicate the assignments.

Use the recommended textbook as the primary source of material.

Each quiz should contain 5-10 questions consisting of a mix of:
- multiple_choice
- short_answer

Multiple choice questions must include exactly four answer choices.

The difficulty should match an introductory university course.

## Output

Return JSON only.

{
    "quizzes": [
        {
            "week": 1,
            "title": "...",
            "type": "weekly",
            "questions": [
                {
                    "type": "multiple_choice",
                    "prompt": "...",
                    "choices": [
                        "...",
                        "...",
                        "...",
                        "..."
                    ],
                    "answer": "..."
                },
                {
                    "type": "short_answer",
                    "prompt": "...",
                    "choices": [],
                    "answer": "..."
                }
            ]
        }
    ]
}
