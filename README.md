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

The agent and the API share one schema. The agent writes rows. The API lists and creates the same records for the current user.

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

### Run the agent

Put your key in a `.env` file in the repository root:

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

Then:

```bash
python -m agent.agent_loop
```

Type a learning goal at the prompt. The agent asks follow-up questions in the terminal when it needs your level, available time, the current date, or your timezone. It then creates the course in `backend/curriculum.db`. The model is `claude-haiku-4-5`, and a run stops after 10 turns.

---

## API

Every route depends on `get_current_user`, which always loads the seeded user above. Requests do not send an `Authorization` header.

| Method | Path | Body | Success |
| --- | --- | --- | --- |
| `GET` | `/courses` | | `200` list of courses |
| `POST` | `/courses` | `name`, `description` | `201` `{"id"}` |
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
| `404` | The course, week, assignment, or quiz is missing, or it belongs to another user |
| `409` | A week with that number already exists on the course |
| `422` | The row violates a database constraint (empty name, invalid type, bad date, non-positive quiz time limit, invalid JSON) |

---

## Agent

`agent/CONTEXT.md` is the system prompt. It tells the model to plan the outline first, then build in order: course, weeks, assignments, and a quiz only for assignments of type `quiz`. Clarifying questions go through the `ask_user` tool, which reads an answer from the terminal.

| Tool | Writes | Returns |
| --- | --- | --- |
| `create_course` | Course name and description for the current user | `course_id` |
| `create_week` | Week number and description on a course | `week_id` |
| `create_assignment` | Type, name, student-facing instructions, rubric, and due date | `assignment_id` |
| `create_quiz` | Time limit and questions on a quiz assignment | `quiz_id` |
| `ask_user` | Nothing | The answer typed at the prompt |

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
- A read/write HTTP API scoped to one seeded user
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
- [x] GitHub Actions CI
- [ ] User authentication
- [ ] Submission storage and grading
- [ ] Frontend
- [ ] Resource retrieval
