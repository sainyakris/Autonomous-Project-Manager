# AutonomousPM

> The project manager that acts, not just advises.

An AI-powered autonomous project management system with **confidence-gated autonomy** — the AI acts independently on high-confidence decisions and escalates low-confidence ones to humans.

## What makes this different

Every competitor (ClickUp, Asana, Monday.com) requires human approval at every step. AutonomousPM acts autonomously when confident and only asks for help when it isn't.

## Features

- **AI task generation** — describe a project in plain English, get a full task breakdown with dependencies and estimates
- **NLP update parsing** — team submits plain English updates, AI extracts progress, blockers and sentiment
- **Confidence-gated autonomy** — AI acts on decisions above 75% confidence, escalates below
- **Priority notifications** — real-time alerts for autonomous actions and escalations
- **Client report generator** — AI writes professional client-facing reports automatically
- **Real-time dashboard** — project health, task status, autonomy score

## Tech Stack

**Backend:** FastAPI, Python 3.12, PostgreSQL 16, SQLAlchemy (async)  
**AI:** Groq API (llama-3.3-70b-versatile)  
**Frontend:** Next.js 14, Tailwind CSS, shadcn/ui  
**Auth:** JWT (python-jose + passlib)

## Getting started

### Prerequisites
- Python 3.12
- PostgreSQL 16
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Backend setup

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
uvicorn app.main:app --reload
```

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### Database setup

```bash
psql postgres
CREATE DATABASE autonomouspm;
CREATE USER pmuser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE autonomouspm TO pmuser;
\q
psql -U yourusername -d autonomouspm -c "GRANT ALL ON SCHEMA public TO pmuser;"
```

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login, get JWT |
| POST | `/api/v1/projects/` | Create project + AI task generation |
| GET | `/api/v1/projects/{id}/tasks` | Get AI-generated tasks |
| POST | `/api/v1/updates/` | Submit NLP update |
| GET | `/api/v1/dashboard/{id}` | Project health dashboard |
| POST | `/api/v1/autonomy/run/{id}` | Run autonomy engine |
| GET | `/api/v1/autonomy/notifications` | Get AI notifications |
| POST | `/api/v1/dashboard/report/generate` | Generate client report |

## Architecture
User Request
↓
FastAPI Backend
↓
AI Agent (Groq/Llama)
↓
Decision Engine
↓
Confidence ≥ 0.75 → Execute autonomously + notify
Confidence < 0.75 → Escalate to human + notify

## Project status

- Phase 1 — Core backend (auth, tasks, NLP, dashboard, reports)
- Phase 2 — Confidence-gated autonomy engine
-Phase 3 — Next.js frontend (in progress)
