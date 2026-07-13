---
name: weekly_goal
version: 0.2
---

## Process

Using the provided course information, generate a week-by-week learning plan.

The number of weeks must exactly equal `duration_weeks`.

Each week should contain:

- a single learning goal
- 3-6 topics to be covered

Requirements:

- Respect `hours_per_week` when determining scope.
- Build concepts sequentially.
- Never introduce material before its prerequisites.
- End the final week with the course reaching the level described in the course description.
- Do not repeat topics unnecessarily.

## Output

Return JSON:

{
  "weekly_goals": [
    {
      "week": 1,
      "goal": "...",
      "topics": [
        "...",
        "..."
      ]
    }
  ]
}
