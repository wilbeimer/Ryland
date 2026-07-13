---
name: course_description
version: 0.2
---

## Current State

The runner will provide the current state as JSON.

Some fields are already populated. Others are `null` or empty.

## Task

Using the current course information:

- Generate a detailed course description.
- Determine the primary academic domain.
- Identify specific subdomains.
- Recommend prerequisites that are genuinely required to succeed in the course.
- Keep the subject matter narrowly focused rather than broad.
- Prefer recommending prerequisites instead of broadening the course scope.

## Output

Return only the following JSON:

{
  "description": "...",
  "domain": "...",
  "subdomains": ["..."],
  "prerequisites": ["..."]
}
