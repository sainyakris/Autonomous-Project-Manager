# AutonomousPM

![CI](https://github.com/sainyakris/Autonomous-Project-Manager/actions/workflows/ci.yml/badge.svg)

An AI project manager that turns plain-English project briefs into dependency-linked task plans and acts on routine decisions on its own, escalating to a human when it isn't confident.

> **Status:** Under active development. Features are being added incrementally and this README will be updated as the project progresses. The original prototype is preserved on the [`legacy-v1`](../../tree/legacy-v1) branch.

## Design

1. **Two-stage intake:** the brief is scored for clarity, and clarifying questions are asked if it's vague.
2. **Context-aware planning:** the LLM produces a task plan with dependencies between tasks.
3. **Hybrid autonomy engine:** rules detect overdue, unassigned and blocked work, and the LLM proposes a fix. Actions run automatically above a confidence threshold and escalate to a human below it. Every action is logged for audit.

LLM output is validated against Pydantic schemas, retried on malformed JSON, and checked against a UUID allow list before anything touches the database.

## Tech stack

Python, FastAPI, PostgreSQL (Docker), SQLAlchemy, Alembic, JWT auth, Pydantic, Llama 3.3 70B via Groq API, pytest, GitHub Actions (tests + gitleaks secret scanning).

## Getting started

```bash
git clone https://github.com/sainyakris/Autonomous-Project-Manager.git
cd Autonomous-Project-Manager/backend

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

docker compose up -d       # start Postgres
cp .env.example .env       # add your own values (e.g. Groq API key)
alembic upgrade head       # run migrations
uvicorn app.main:app --reload   # start the server (adjust path if needed)
pytest                     # run tests
```