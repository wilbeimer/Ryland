---
name: course_length
version: 0.1
---

## Inputs
- 01_course_description (course description, domain, subdomains)

## Process
Based on the course description and domain, estimate how many weeks this course should take for a student who has already taken the prerequisites and how many hours per week a student should expect to spend.

## Output
Return as JSON:
{
    "weeks": 12,
    "hours_per_week": 5,
    "reasoning": "..."
}
