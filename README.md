![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688)
![CI](https://github.com/wilbeimer/Ryland/actions/workflows/ci.yml/badge.svg)
# Ryland

> An AI-powered course builder that turns a learner's goals into a structured curriculum and stores it in SQLite.

Ryland takes a learning goal and builds a course around it: weeks, text assignments, and quizzes, each with a rubric a later grader can use. A tool-calling agent plans the course and writes it through the same database the API reads.

Built with **Python, FastAPI, SQLite, and the Anthropic API**.

---

## Table of Contents

- [Why I Built It](#why-i-built-it)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [API](#api)
- [Agent](#agent)
- [Tech Stack](#tech-stack)
- [Project Status](#project-status)
- [Roadmap](#roadmap)

---

## Why I Built It

One of the biggest challenges when learning a new subject isn't finding information—it's deciding **what to learn next**.

I built **Ryland** to automate that planning process. Instead of manually organizing topics, practice, and checks for understanding into a roadmap, you describe what you want to learn. Ryland generates a course with weeks, assignments, and quizzes fitted to your goal, level, and time.

It is also a place to try agentic planning: one model, a narrow set of tools, and a database that is the source of truth. The agent does not invent IDs or write files. It creates a course, then weeks, then assignments, then quizzes, using the IDs each tool returns.

---

## Features

- Tool-calling course builder (Claude)
- HTTP job to start a build and poll its progress
- Courses, weeks, text assignments, and quizzes
- Rubrics stored with each assignment
- Quizzes with short-answer and multiple-choice questions
- Public quiz responses that omit correct answers
- Ownership checks so each user only sees their own courses
- FastAPI REST API
- SQLite persistence
- GitHub Actions CI (Ruff, Black, Pytest)

---

## Architecture

```text
        Learner goal
              │
              ├──────────────────────────────┐
              ▼                              ▼
   POST /courses/generate          python -m agent.agent_loop
   goal, level, time, timezone     terminal prompt + ask_user
              │                              │
              └──────────────┬───────────────┘
                             ▼
                    agent/agent_loop.py
                    (Claude + CONTEXT.md)
                             │
                             ▼
                       agent/tools.py
                  create_course / create_week
                  create_assignment / create_quiz
                       ask_user
                             │
                             ▼
                        backend/db.py
                        curriculum.db
                             │
                             ▼
                     backend/endpoints.py
                        FastAPI routes
```

The agent and the API share one schema. The agent writes rows through the same database functions the API uses. The API lists and creates those records for the current user, and can start a build.

A course belongs to a user. A week belongs to a course, and week numbers are unique within that course. An assignment is either `text` or `quiz` and belongs to a week. A quiz belongs to one assignment and stores a time limit plus questions. Correct answers stay in the database. The quiz read endpoint returns the public shape, which leaves them out.

Authentication is a stand-in. Every request resolves to a single seeded user. There is no login flow yet.

---

## Getting Started

### Prerequisites

- Python 3.12 (the version CI runs)
- An Anthropic API key, only if you want to run the course-building agent

### Install

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Seed the database

The API and the agent both act as one fixed user. Create the database and that user before anything else:

```bash
python -m backend.db
```

This writes `backend/curriculum.db` and inserts:

| Field | Value |
| --- | --- |
| id | `00000000-0000-0000-0000-000000000001` |
| email | `test@mail.com` |
| password | `password` |

The password is stored as plain text. This seed exists so local runs have a user to attach courses to. It is not an authentication system.

### Run the API

```bash
uvicorn backend.endpoints:app --reload
```

The API listens on `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### Call it from a local page

A Vite dev server on another port is a different origin, so the API sends CORS headers. The default allows `http://localhost:5173` and `http://127.0.0.1:5173`. Set a comma-separated list to change that:

```bash
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Put `CORS_ORIGINS` and `ANTHROPIC_API_KEY` in a `.env` file in the repository root. The API loads that file on startup. Restart uvicorn after editing it. Run a single worker. Generation jobs live in that process and are gone after a restart or a reload.

### Generate a course over HTTP

`POST /courses/generate` takes the details the terminal agent asks for, starts a build, and returns immediately with a job id. Poll `GET /courses/generate/{job_id}` until `status` is `succeeded`, `incomplete`, or `failed`. On `succeeded` or `incomplete` the body includes `course_id` and the course `name` and `description`. Weeks, assignments, and quizzes are the existing read routes. A second POST returns `409` while that user's worker is still running. A build still `pending` or `running` after 15 minutes is asked to stop. The worker checks that flag before each model turn and each tool call, then stops. A call already in flight can finish. The job stays on the `409` until the worker exits, then `status` is `failed`. If a course was saved before the stop, that failed job still includes its `course_id`.

```bash
curl -s -X POST http://localhost:8000/courses/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "goal": "Learn SQL joins well enough to write reports",
    "level": "beginner, comfortable with SELECT",
    "time_available": "4 hours a week for 3 weeks",
    "timezone": "America/New_York"
  }'
```

The response is `202` with `job_id` and `status: "pending"`. The `Location` header points at the status route.

```bash
curl -s http://localhost:8000/courses/generate/<job_id>
```

While the job runs, `detail` moves through the turns (`Turn 2`, `Using create_week`). That is the progress a page can show. The build calls Claude and can take a while. Polling keeps this to ordinary requests: the page does not hold a stream open, and refreshing the status call does not start a second build. The job is only in memory. Finished jobs are dropped after 30 minutes, and only the 20 newest finished jobs are kept.

`timezone` must be an IANA name such as `America/New_York`. Anything else is `422` and does not start a build. The server uses that zone, together with the current time, so the agent can set due dates. The seeded user from `python -m backend.db` has to exist first. The course is saved for that user. This path does not read from the terminal. If the model still calls `ask_user`, the tool answers from the request instead of waiting for input.

`succeeded` means the agent finished and created a course. `incomplete` means it hit the turn cap after creating the course: `course_id` is set, and `detail` says the course may be missing weeks, assignments, or quizzes. `error` is set only when `status` is `failed`. If it never creates a course, `status` is `failed` and `error` says why.

### Run the agent in the terminal

The CLI still works. Put your key in `.env` if it is not already there:

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

Then, from the repository root:

```bash
python -m agent.agent_loop
```

Type a learning goal at the prompt. The agent asks follow-up questions in the terminal when it needs your level, available time, the current date, or your timezone. It then creates the course in `backend/curriculum.db`. The model is `claude-haiku-4-5`, and a run stops after 10 turns.

### Test the generate endpoint

The generate test mocks the agent, so it does not need an API key. HTTPX is in `requirements.txt` because `TestClient` imports it. Pytest is not:

```bash
pip install pytest
pytest tests/test_generate.py
```

---

## API

Every route depends on `get_current_user`, which always loads the seeded user above. Requests do not send an `Authorization` header.

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| `GET` | `/courses` | | `200` list of courses |
| `POST` | `/courses` | `name`, `description` | `201` `{"id"}` |
| `POST` | `/courses/generate` | `goal`, `level`, `time_available`, `timezone` | `202` job `{job_id, status}` |
| `GET` | `/courses/generate/{job_id}` | | `200` job; `course_id` and `course` when `succeeded` or `incomplete` |
| `GET` | `/courses/{course_id}/weeks` | | `200` weeks, ordered by `week_number` |
| `POST` | `/courses/{course_id}/weeks` | `week_number`, `description` | `201` `{"id"}` |
| `GET` | `/weeks/{week_id}/assignments` | | `200` list of assignments |
| `POST` | `/weeks/{week_id}/assignments` | `type`, `name`, `description`, `rubric`, `due_date` | `201` `{"id"}` |
| `GET` | `/assignments/{assignment_id}/quiz` | | `200` quiz without correct answers |
| `POST` | `/assignments/{assignment_id}/quiz` | `time_limit`, `questions` | `201` `{"id"}` |

`week_number` starts at 1. Two weeks in the same course cannot share a number.

`type` is `text` or `quiz`. `due_date` is an ISO 8601 datetime. `rubric` is a JSON object. The agent writes rubrics as `{ "criteria": [{ "name", "description", "points" }] }`. The API stores whatever object it receives, as long as it is valid JSON.

`time_limit` is a duration. The database stores it as a positive number of seconds. Each question has `question_type` (`short answer` or `multiple choice`), `prompt`, and `correct_answer`. Multiple-choice questions also include `options`. `GET` quiz responses drop `correct_answer`.

### Errors

| Status | When |
| --- | --- |
| `404` | The course, week, assignment, quiz, or generation job is missing, or it belongs to another user |
| `409` | A week with that number already exists on the course, or a course build is already in progress |
| `422` | The row violates a database constraint (empty name, invalid type, bad date, non-positive quiz time limit, invalid JSON), or a generate field is missing, blank, or not a real IANA timezone |

---

## Agent

`agent/CONTEXT.md` is the system prompt. It tells the model to plan the outline first, then build in order: course, weeks, assignments, and a quiz only for assignments of type `quiz`. Clarifying questions go through the `ask_user` tool.

From the terminal, `ask_user` reads an answer with `input()`. From `POST /courses/generate`, the request already carries the goal, level, time available, and timezone, and the server adds the current time in that timezone. `ask_user` answers from that brief and does not read the terminal. The model is the same either way: `claude-haiku-4-5`, with `ANTHROPIC_API_KEY`.

| Tool | Writes | Returns |
| --- | --- | --- |
| `create_course` | Course name and description for the current user | `course_id` |
| `create_week` | Week number and description on a course | `week_id` |
| `create_assignment` | Type, name, student-facing instructions, rubric, and due date | `assignment_id` |
| `create_quiz` | Time limit and questions on a quiz assignment | `quiz_id` |
| `ask_user` | Nothing | The answer typed at the prompt, or the generate-request brief |

Tool errors come back to the model so it can correct the input and retry. The agent does not search the web. `CONTEXT.md` tells it not to invent URLs or titles.

---

## Tech Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic
- Uvicorn

### Database

- SQLite (`backend/curriculum.db`)

### AI

- Anthropic API (`claude-haiku-4-5`)
- Tool use defined in `agent/tools.py`
- System prompt in `agent/CONTEXT.md`

### DevOps

- GitHub Actions on `main` and `develop` (`.github/workflows/ci.yml`)
- Ruff
- Black
- Pytest with coverage on `backend`

---

## Project Status

Active development. What works today:

- Course, week, assignment, and quiz persistence
- A tool-calling agent that fills those tables from a learning goal
- `POST /courses/generate` to start that agent from a page, plus a status poll
- A read/write HTTP API scoped to one seeded user
- CORS for a local Vite origin
- CI for lint, format, and tests

Not built yet:

- Real authentication (the current user is hard-coded)
- A grading pipeline (`Submission` is modeled in `backend/models.py` and has no table or routes)
- A frontend
- Retrieval over external learning resources

---

## Roadmap

- [x] Course, week, assignment, and quiz schema
- [x] FastAPI CRUD for that schema
- [x] Tool-calling course builder
- [x] SQLite persistence
- [x] HTTP course generation (job id and status poll)
- [x] GitHub Actions CI
- [ ] User authentication
- [ ] Submission storage and grading
- [ ] Frontend
- [ ] Resource retrieval
