import json
import re
from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


async def generate_tasks_from_description(
    project_name: str,
    description: str,
    team_skills: list[str] = None,
    deadline_days: int = None,
) -> dict:
    skills_context = f"Available team skills: {', '.join(team_skills)}" if team_skills else ""
    deadline_context = f"Target deadline: {deadline_days} days from now" if deadline_days else ""

    prompt = f"""You are an expert project manager. Break down this project into executable tasks.

Project: {project_name}
Description: {description}
{skills_context}
{deadline_context}

Return ONLY valid JSON with no markdown, no explanation, no code fences. Use this exact structure:
{{
  "summary": "one sentence project summary",
  "total_estimated_hours": 0,
  "risk_level": "low",
  "tasks": [
    {{
      "id": "t1",
      "title": "Task title",
      "description": "What needs to be done",
      "priority": "medium",
      "estimated_hours": 4,
      "required_skills": ["skill1"],
      "dependencies": [],
      "phase": "planning"
    }}
  ]
}}

Rules:
- Break into tasks of 2-8 hours each
- priority must be one of: low, medium, high, critical
- phase must be one of: planning, development, testing, deployment
- dependencies is a list of task id strings
- Return at least 5 tasks
- Return ONLY the JSON, nothing else"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


async def parse_team_update(
    raw_text: str,
    task_title: str,
    current_progress: float = 0.0,
) -> dict:
    prompt = f"""You are parsing a team member's project update. Extract structured data.

Task: {task_title}
Current progress: {int(current_progress * 100)}%
Update: "{raw_text}"

Return ONLY valid JSON with no markdown:
{{
  "progress": 0.0,
  "blocker": null,
  "blocker_severity": null,
  "sentiment": "neutral",
  "key_insight": "one sentence summary",
  "needs_human_attention": false
}}

Rules:
- progress is a float between 0.0 and 1.0
- sentiment must be one of: positive, neutral, negative
- blocker_severity must be one of: minor, moderate, critical, or null
- Return ONLY the JSON, nothing else"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


async def generate_client_report(
    project_name: str,
    progress: float,
    completed_tasks: list[str],
    upcoming_tasks: list[str],
    risks: list[str] = None,
) -> dict:
    prompt = f"""Write a professional project status report for a client.

Project: {project_name}
Overall progress: {int(progress * 100)}%
Completed this period: {json.dumps(completed_tasks)}
Coming up next: {json.dumps(upcoming_tasks)}
{f"Risks to communicate: {json.dumps(risks)}" if risks else "No risks to communicate."}

Return ONLY valid JSON with no markdown:
{{
  "subject": "email subject line",
  "report": "full report text in clear professional language, no technical jargon, no internal details",
  "tone": "positive",
  "key_wins": ["win 1", "win 2"],
  "next_milestone": "what the client should expect next"
}}

Rules:
- tone must be one of: positive, neutral, cautious
- No internal task IDs, developer names, or technical issues
- Keep it concise and professional
- Return ONLY the JSON, nothing else"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)