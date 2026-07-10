---
name: assignments
version: 0.2
---

## Process

Create assignments that help students achieve this week's learning goal.

Requirements:

- Base assignments on this week's topics.
- Follow the recommended textbook when appropriate.
- Keep the total estimated workload within `hours_per_week`.
- Assignments should build practical understanding of the week's material.
- Generate between 2 and 3 assignments.
- Use a variety of assignment types when appropriate.

Allowed assignment types:

- reading
- written
- coding
- project
- discussion
- checklist
- practice

## Output

Return JSON:

{
    "assignments": [
        {
            "title": "...",
            "type": "...",
            "description": "...",
            "requirements": [
                "...",
                "..."
            ]
        }
    ]
}
