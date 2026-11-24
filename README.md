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
- Username and password sign-in, with email used only to confirm the account
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

Sign-in uses a username and password. Email is collected at sign-up and is only used to confirm the account. A signed-in request sends `Authorization: Bearer <token>`. The token is an opaque session stored in SQLite.

---

## Getting Started

### Prerequisites

- Python 3.12 (the version CI runs)
- Node.js 22 (for the frontend)
- An Anthropic API key, only if you want to run the course-building agent

### Install

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Seed the database

The API and the terminal agent can attach courses to one local account. That account is not created unless you opt in. Put this in `.env` (it stays off in any deployed environment):

```bash
RYLAND_DEV_SEED=1
```

Then create the database. `python -m backend.db` loads `.env`:

```bash
python -m backend.db
```

With the flag set, this writes `backend/curriculum.db` and inserts a verified user you can sign in with:

| Field | Value |
| --- | --- |
| id | `00000000-0000-0000-0000-000000000001` |
| username | `test` |
| email | `test@mail.com` |
| password | `password` |

The password is stored as a scrypt hash. Email is not a login. Re-run the same command, still with `RYLAND_DEV_SEED=1`, on an older database to hash a plaintext seed password and set the username. Without the flag, startup does not create or auto-verify `test` / `password`. The terminal agent still writes courses for this user when the account exists, so they show up when you sign in as `test`.

### Run the API

```bash
uvicorn backend.endpoints:app --reload
```

The API listens on `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### Run the frontend

For v1 the frontend is localhost-only. Start the API, then the Vite dev server:

```bash
# terminal 1 — API
uvicorn backend.endpoints:app --reload

# terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The home page asks you to sign in. After seeding with `RYLAND_DEV_SEED=1`, use username `test` and password `password`, or create an account. New accounts stay signed out until the verification link is opened (`/verify-email?token=...`). With SMTP unset, that link is printed in the API terminal. If sign-in says the email is not confirmed yet, use Resend verification email on that page. Signing up again with the same username and email works once that link has expired.

The `/api` proxy only works on the Vite dev server in this setup: it forwards `/api` to `http://127.0.0.1:8000` so the page can call the API without CORS. A static `dist/` deploy does not get that proxy; set `VITE_API_BASE_URL` to the API origin (for example `http://localhost:8000`) before `npm run build` if you need that path. The browser stores the session token in `localStorage` and sends `Authorization: Bearer`.

### Call it from a local page

If the page talks to the API on another origin directly (not through the Vite `/api` proxy), the API sends CORS headers. The default allows `http://localhost:5173` and `http://127.0.0.1:5173`. Set a comma-separated list to change that:

```bash
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Put `CORS_ORIGINS` and `ANTHROPIC_API_KEY` in a `.env` file in the repository root. The API loads that file on startup. Restart uvicorn after editing it. Run a single worker. Generation jobs live in that process and are gone after a restart or a reload.

### Email verification

Sign-up sends a confirmation link. The account cannot sign in until that link is opened. Copy `.env.example` to `.env` and leave the SMTP variables empty to print the link in the API console. To send mail, set a free SMTP account (a Gmail address with an [app password](https://support.google.com/accounts/answer/185833) works):

| Variable | Purpose |
| --- | --- |
| `SMTP_HOST` | SMTP server. Unset means log the link instead of sending. |
| `SMTP_PORT` | Default `587` (STARTTLS). Use `465` for implicit TLS. |
| `SMTP_USER` | SMTP username, often the mailbox address. |
| `SMTP_PASSWORD` | SMTP password or app password. Never commit this. |
| `SMTP_FROM` | From address. Falls back to `SMTP_USER`. |
| `APP_PUBLIC_URL` | Origin used in the link. Default `http://localhost:5173`. |

`.env` is gitignored. Do not commit real passwords.

### Generate a course over HTTP

`POST /courses/generate` takes the details the terminal agent asks for, starts a build, and returns immediately with a job id. Poll `GET /courses/generate/{job_id}` until `status` is `succeeded`, `incomplete`, or `failed`. On `succeeded` or `incomplete` the body includes `course_id` and the course `name` and `description`. Weeks, assignments, and quizzes are the existing read routes. A second POST returns `409` while that user's worker is still running. A build still `pending` or `running` after 15 minutes is asked to stop. The worker checks that flag before each model turn and each tool call, then stops. A call already in flight can finish. The job stays on the `409` until the worker exits, then `status` is `failed`. If a course was saved before the stop, that failed job still includes its `course_id`.

```bash
curl -s -X POST http://localhost:8000/courses/generate \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{
    "goal": "Learn SQL joins well enough to write reports",
    "level": "beginner, comfortable with SELECT",
    "time_available": "4 hours a week for 3 weeks",
    "timezone": "America/New_York"
  }'
```

The response is `202` with `job_id` and `status: "pending"`. The `Location` header points at the status route.

```bash
curl -s http://localhost:8000/courses/generate/<job_id> \
  -H 'Authorization: Bearer <token>'
```

While the job runs, `detail` moves through the turns (`Turn 2`, `Using create_week`). That is the progress a page can show. The build calls Claude and can take a while. Polling keeps this to ordinary requests: the page does not hold a stream open, and refreshing the status call does not start a second build. The job is only in memory. Finished jobs are dropped after 30 minutes, and only the 20 newest finished jobs are kept.

`timezone` must be an IANA name such as `America/New_York`. Anything else is `422` and does not start a build. The server uses that zone, together with the current time, so the agent can set due dates. The course is saved for the signed-in user, so the request needs `Authorization: Bearer <token>` from `POST /auth/signin`. This path does not read from the terminal. If the model still calls `ask_user`, the tool answers from the request instead of waiting for input. The terminal agent (`python -m agent.agent_loop`) still writes as the seeded `test` user and does not use the HTTP session.

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

Course routes depend on `get_current_user`, which reads `Authorization: Bearer <token>` from `POST /auth/signin`. Sign-up, verify, and sign-in are public. Email is not accepted as a username.

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| `POST` | `/auth/signup` | `username`, `password`, `email` | `201` account, `email_verified: false`. Sends or logs a confirmation link. An unverified account with an expired link can sign up again. |
| `POST` | `/auth/resend` | `username`, `password` | `200` sends or logs a new link for an unverified account |
| `POST` | `/auth/verify` | `token` | `200` `email_verified: true` |
| `POST` | `/auth/signin` | `username`, `password` | `200` `{token, user}` after the email is confirmed |
| `POST` | `/auth/signout` | | `204` |
| `GET` | `/auth/me` | | `200` the signed-in user, without the password |
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
| `401` | A protected route has no session, or the username and password do not match |
| `403` | The account exists but the email is not confirmed yet |
| `404` | The course, week, assignment, quiz, or generation job is missing, or it belongs to another user |
| `409` | A week with that number already exists on the course, a course build is already in progress, or the username or email is already registered |
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

### Frontend

- Vite
- React 19
- TypeScript

### DevOps

- GitHub Actions on `main` and `develop` (`.github/workflows/ci.yml`)
- Ruff
- Black
- Pytest with coverage on `backend`
- Frontend lint and production build

---

## Project Status

Active development. What works today:

- Course, week, assignment, and quiz persistence
- A tool-calling agent that fills those tables from a learning goal
- `POST /courses/generate` to start that agent from a page, plus a status poll
- A read/write HTTP API scoped to the signed-in user
- Username/password sign-in and email confirmation over SMTP (or the API console when SMTP is unset)
- CORS for a local Vite origin
- A TypeScript courses home page that lists courses from the API
- Sign-in, sign-up, and email verification pages
- CI for lint, format, backend tests, and the frontend build

Not built yet:

- Password reset, OAuth, and rate limiting
- A grading pipeline (`Submission` is modeled in `backend/models.py` and has no table or routes)
- Course detail / generate / assignment pages beyond the home list
- Retrieval over external learning resources

---

## Roadmap

- [x] Course, week, assignment, and quiz schema
- [x] FastAPI CRUD for that schema
- [x] Tool-calling course builder
- [x] SQLite persistence
- [x] HTTP course generation (job id and status poll)
- [x] GitHub Actions CI
- [x] User authentication (username, password, email confirmation)
- [ ] Submission storage and grading
- [x] Courses home frontend
- [ ] Course detail and generate UI
- [ ] Resource retrieval
