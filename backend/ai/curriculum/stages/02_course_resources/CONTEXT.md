---
name: course_resources
version: 0.2
---

## Current State

The runner provides the current curriculum state as JSON.

Use the course information, including its title, description, domain, and subdomains, to recommend the most appropriate textbook.

## Task

Recommend a single academic textbook that would serve as the primary text for this course.

Choose a textbook that is:

- Widely used in university courses
- Well regarded by instructors
- Appropriate for the course level
- Closely aligned with the course topics

## Output

Return only the following JSON:

{
  "textbook": {
    "title": "...",
    "authors": ["..."],
    "isbn": "...",
    "link": "..."
  }
}
