---
name: course_description
version: 0.1
---

## Inputs
- course_name = {course_name}
- course_description = {course_description}

## Process
Generate a detailed description of the {course_name} course based on the following description provided by the user: {course_description}. Include the course's academic domain, subdomains, and prerequisites a student should have. Keep subject matter narrow, prefering to recommend prerequisites when needed to fully understand the course. Be very specific about course material, don't generalize description.

## Output
Return as JSON:
{
    "description": "...",
    "domain": "...",
    "subdomains": ["..."],
    "prerequisites": ["..."]
}
