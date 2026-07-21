![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688)
![React](https://img.shields.io/badge/React-Frontend-61DAFB)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)
![CI](https://github.com/wilbeimer/Ryland/actions/workflows/ci.yml/badge.svg)
# Ryland

> An AI-powered curriculum generation platform that builds personalized learning plans using an agent-driven planning workflow.

Ryland transforms high-level learning goals into structured curricula, assignments, quizzes, and educational resources. A collection of specialized AI agents collaborates to plan learning objectives, generate assessments, retrieve supporting resources, and evaluate completed work through a separate grading pipeline.

The system is built around a shared application state, allowing each planning component to focus on a single responsibility while contributing to a complete curriculum.

Built with **Python, FastAPI, React, SQLite, Docker, and Groq LLMs**.

---

## Table of Contents

- [Why I Built It](#why-i-built-it)
- [Features](#features)
- [Screenshots](#screenshots)
- [Architecture](#architecture)
- [Engineering Decisions](#engineering-decisions)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Status](#project-status)
- [Roadmap](#roadmap)

---

## Why I Built It

One of the biggest challenges when learning a new subject isn't finding information—it's deciding **what to learn next**.

I built **Ryland** to automate that planning process. Instead of manually organizing tutorials, articles, documentation, and projects into a coherent learning roadmap, users simply describe what they want to learn. Ryland then generates a personalized curriculum complete with weekly goals, assignments, quizzes, and curated learning resources.

Beyond solving that problem, Ryland serves as a platform for exploring agentic AI systems. It experiments with decomposing complex planning tasks into smaller reasoning steps while integrating external tools and structured application state.

---

## Features

- AI-generated personalized curricula
- Assignment and quiz generation
- AI-powered grading and feedback
- Shared state-based workflow orchestration
- Modular planning pipeline
- YouTube resource retrieval
- FastAPI REST API
- React frontend
- SQLite persistence
- Dockerized development environment
- GitHub Actions continuous integration

---

## Screenshots

### Dashboard

<img width="795" height="913" alt="Dashboard Image" src="https://github.com/user-attachments/assets/cbbad31e-cb48-47a6-8ef7-51f35ad574dc" />

### Generated Curriculum

<img width="746" height="998" alt="Generated Curriculum Image" src="https://github.com/user-attachments/assets/b8eb3d56-1878-41fa-a6db-98b373be8fb2" />

### Assignment View

<img width="750" height="972" alt="Assignment View Image" src="https://github.com/user-attachments/assets/1f7f457b-f05e-4023-9cc2-ac34c922b08f" />

---

## Getting Started

### Docker (Recommended)

```bash
docker compose up --build
```

Frontend:

```
http://localhost:8080
```

Backend API:

```
http://localhost:8000
```

---

### Local Development

#### Prerequisites

- Python 3.11+
- Node.js
- Groq API Key
- YouTube Data API Key

#### Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```
http://localhost:5173
```

---

## Architecture

### Curriculum Generation

```text
            User Goal
                 │
                 ▼
        Curriculum Planner
                 │
                 ▼
        Shared RylandState
                 │
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
 Generate   Retrieve   Generate
 Objectives Resources Assignments
      │          │          │
      └──────────┼──────────┘
                 ▼
        Generate Assessments
                 │
                 ▼
        Completed Curriculum
                 │
                 ▼
          React Frontend
```

### Assignment Grading

```text
Student Submission
        │
        ▼
   Analyze Work
        │
        ▼
 Generate Score
        │
        ▼
 Generate Feedback
```

Ryland is built around a shared `RylandState` object that acts as the central source of truth throughout the planning process. Rather than passing intermediate JSON files between components, each planning step reads from and updates the shared state.

This architecture reduces unnecessary file I/O, simplifies data flow, and makes it easier to introduce new planning capabilities without redesigning the overall workflow.

---

## Engineering Decisions

Rather than relying on a single prompt to generate an entire curriculum, Ryland decomposes the problem into a collection of focused planning tasks. Each planning component has a narrow responsibility, improving consistency while making failures easier to debug and individual behaviors easier to refine.

The planning workflow is orchestrated through a shared `RylandState` object, eliminating intermediate files and providing a single source of truth for the application. This state-centric design also makes the system easier to extend as new planning capabilities are introduced.

The backend is organized around modular services and external tool integrations. As the project evolves, planning components are being refactored into reusable AI tools that can be orchestrated more dynamically, allowing the system to move beyond a strictly sequential pipeline.

---

## Tech Stack

### Frontend

- React

### Backend

- Python
- FastAPI
- Pydantic

### Database

- SQLite

### AI

- Groq API
- Multi-agent orchestration
- Structured prompting

### Infrastructure

- Docker
- Docker Compose
- Nginx

### DevOps

- GitHub Actions
- Ruff
- Black
- Pytest

### External APIs

- YouTube Data API

---

## Project Status

🚧 **Active Development**

Current focus:

- Tool-based agent architecture
- Cloud deployment
- User authentication
- Vector search (RAG)
- Enhanced grading pipeline

---

## Roadmap

- [x] AI curriculum generation
- [x] Assignment generation
- [x] Quiz generation
- [x] AI grading pipeline
- [x] Shared application state
- [x] Docker deployment
- [x] GitHub Actions CI
- [ ] Tool-calling planning agents
- [ ] Vector database integration
- [ ] User authentication
- [ ] Cloud deployment
