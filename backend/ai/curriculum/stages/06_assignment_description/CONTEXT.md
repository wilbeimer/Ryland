---
name: assignment_description
version: 0.2
loop_over: assignments
merge_item: true
depends_on:
  - 02_course_resources
  - 04_weekly_goal
  - 05_assignments
---

## Process

You are expanding an existing assignment.

Using:
- the assignment title and type
- the week's learning goal
- the week's topics
- the recommended textbook
- the overall course description

write a detailed assignment that directly supports that week's learning objectives.

Requirements:
- Follow the progression established by previous weeks.
- Assume the student is using the recommended textbook.
- Be specific about what the student should produce.
- Do not mention LMS platforms (Canvas, Blackboard, etc.).
- Do not include grading information.
- Keep the work realistic for the allotted weekly study time.

## Output

Return JSON only.

{
    "description": "...",
    "requirements": [
        "...",
        "...",
        "..."
    ]
}
