---
name: assignments
version: 0.1
---

## Process
For each week in weekly_goals, create a set of assignments that progress the student toward that week's goal and follow the textbook.
Make sure total assignment time fits within hours_per_week.
Return ALL weeks as a single flat list.
Generate no more than 20 assignments total across all weeks.

## Output
Return as JSON:
{
    "assignments": [
        {
            "week": 1,
            "title": "...",
            "type": "written | checklist"
        }
    ]
}
