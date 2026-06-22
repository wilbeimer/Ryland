---
name: assignments
version: 0.2
---

## Inputs
- 01_course_description (description, domain, subdomains, prerequisites)
- 02_course_length (weeks, hours per week, reasoning)
- 03_weekly_goals (week, goal, topics)

## Process
For each week in weekly_goals, create a set of assignments that progress the student toward that week's goal.
Make sure total assignment time fits within hours_per_week.
Return ALL weeks as a single flat list.

## Output
Return as JSON:
{
    "assignments": [
        {
            "week": 1,
            "title": "...",
            "type": "quiz | written | checklist"
        }
    ]
}
