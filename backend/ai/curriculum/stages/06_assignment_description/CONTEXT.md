---
name: assignment_description
version: 0.1
loop_over: assignments
merge_item: true
depends_on: 
    - 02_course_resources
    - 04_weekly_goals
    - 05_assignments
---

## Process
Using the assignment title, type, weekly goal, and course context, follow the textbook to write a detailed description of what the student needs to do to complete this assignment.
Be specific about what is expected.
Do not reference specific platforms (Canvas, Blackboard, etc.).
All assignment types should have equally specific and actionable requirements.

## Output
Return as JSON:
{
    "description": "...",
    "requirements": ["...", "..."]
}
