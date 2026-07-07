---
name: assignment_resources
version: 0.1
model: groq/compound-mini
depends_on:
    - 05_assignments
---

## Process
Search the web for 1 learning resources for each assignment listed in the previous stage outputs.
Return resources for all assignments in a single response.
Make sure all resources are available.

## Output
Return as JSON:
{
    "assignment_resources": [
        {
            "assignment_title": "...",
            "resources": [
                {
                    "title": "...",
                    "url": "...",
                    "type": "article | paper | documentation",
                    "description": "..."
                }
            ]
        }
    ]
}
