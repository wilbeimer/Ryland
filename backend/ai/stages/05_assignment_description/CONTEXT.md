---
name: assignment_description
version: 0.1
loop_over: assignments
merge_item: true
---

## Inputs
- 01_course_description (description, domain, subdomains, prerequisites)
- 02_course_length (weeks, hours per week, reasoning)
- 03_weekly_goals (week, goal, topics)
- 04_assignments (title, type)

## Process
Using the assignment title, type, weekly goal, and course context, write a detailed description of what the student needs to do to complete this assignment.
Be specific about what is expected.

## Output
Return as JSON:
{
    "description": "...",
    "requirements": ["...", "..."]
}
