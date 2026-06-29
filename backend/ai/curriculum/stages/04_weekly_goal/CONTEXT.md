---
name: weekly_goal
version: 0.1
---

## Process
For each week in the course, create a clear learning goal and a list of topics to cover that week.
Ensure logical progression so students are never introduced to a concept before its prerequisites are covered.
Account for the number of hours per week when scoping each week's content.

## Output
Return as JSON:
{
    "weekly_goals": [
        {
            "week": 1,
            "goal": "...",
            "topics": ["...", "..."]
        }
    ]
}
