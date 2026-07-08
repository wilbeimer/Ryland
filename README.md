# Personal Curriculum

> An AI-powered curriculum generation platform that builds personalized learning plans using a staged, multi-agent workflow.

Personal Curriculum transforms high-level learning goals into structured curricula, assignments, quizzes, and educational resources. Specialized AI agents collaborate to plan the curriculum, retrieve supporting content from external APIs, and generate personalized feedback through a separate grading pipeline.

Built with **Python, FastAPI, React, SQLite, and Groq LLMs**.des an AI grading pipeline that analyzes student submissions, assigns scores, and generates personalized feedback using a staged reasoning process.


---

## Table of Contents

- [Why I Built It](#why-i-built-it)
- [Features](#features)
- [Screenshots](#screenshots)
- [Agent Workflow](#agent-workflow)
- [Engineering Decisions](#engineering-decisions)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Status](#project-status)

---

## Why I Built It

One of the biggest challenges when learning a new subject isn't finding information—it's deciding **what to learn next**.

I built Personal Curriculum to automate that planning process. Instead of manually organizing tutorials, articles, and projects into a coherent roadmap, users describe what they want to learn, and the system generates a structured curriculum complete with assignments and supporting resources.

This project also serves as a way to explore agentic AI systems that combine LLM reasoning with external tools.

---

## Features

- Multi-stage agent pipeline
- Curriculum and learning objective generation
- Assignment and quiz generation
- AI-powered grading and feedback
- YouTube resource retrieval
- REST API built with FastAPI
- React frontend
- Persistent curriculum storage with SQLite

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

### Prerequisites

- Python 3.11+
- Node.js
- Groq API Key
- YouTube Data API Key

### Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

The application will be available at:

```
http://localhost:5173
```

---

## Agent Workflow

### Curriculum Generation

```text
User Goal
    │
    ▼
Curriculum Runner
    │
    ▼
Course Description
    │
    ▼
Course Resources
    │
    ▼
Course Length
    │
    ▼
Weekly Goals
    │
    ▼
Assignments
    │
    ▼
Assignment Details
    │
    ▼
Quiz Generation
    │
    ▼
Resource Generation
    │
    ▼
Final Curriculum
    │
    ▼
React Frontend
```

### Assignment Grading

```text
Student Submission
        │
        ▼
 Analyze
        │
        ▼
 Score
        │
        ▼
 Feedback
```

Each stage is responsible for a single planning task and receives the output of the previous stage as context.

This staged architecture produces more consistent results than attempting to generate an entire curriculum in a single prompt while making individual components easier to test, modify, and extend.

---

## Engineering Decisions

Rather than relying on a single LLM prompt, the curriculum generator uses a staged pipeline in which each agent performs a narrowly defined task. This approach improves consistency, simplifies debugging, and allows individual stages to evolve independently.

The backend is organized around modular services so additional planning stages or retrieval tools can be added without changing the overall pipeline.

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
- Prompt Engineering
- Multi-agent orchestration

### External APIs
- YouTube Data API

### Development
- Git
- Make

---

## Project Status

🚧 Active Development

Current focus:

- Improved grading pipeline
- Cloud deployment
- GitHub Actions CI

