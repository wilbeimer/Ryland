---
name: course_length
version: 0.2
---

## Current State

The runner provides the current curriculum state as JSON.

Use the current course information, including its description, domain, subdomains, and prerequisites, to estimate an appropriate course length.

## Task

Determine:

- The total duration of the course in weeks.
- The expected number of study hours per week.

Assume the student has already completed the recommended prerequisites.

Guidelines:

- Most introductory courses should be between 6 and 10 weeks.
- Do not generate more than 10 weeks.
- Choose a workload that is realistic for an online learner.

## Output

Return only the following JSON:

{
  "duration_weeks": 8,
  "hours_per_week": 5
}
