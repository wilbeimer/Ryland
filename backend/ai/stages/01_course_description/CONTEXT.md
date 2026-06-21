---
name: course_description
version: 0.1
model: llama-3.3-70b-versatile
---

## Inputs
- course_name = {course_name}

## Process
Generate a detailed description of the {course_name} course, its academic domain, subdomains, and prerequisites a student should have. Keep subject matter narrow, prefering to recommend prerequisites when needed to fully understand the course. Be very specific about course material, don't generalize description.

## Output
Return as JSON:
{
    "description": "...",
    "domain": "...",
    "subdomains": ["..."],
    "prerequisites": ["..."]
}
