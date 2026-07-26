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


async def analyze_project_description(
    description: str,
    project_name: str,
) -> dict:
    prompt = f"""You are an expert project manager conducting an initial project intake.

A client has submitted the following project:

Project Name: {project_name}
Description: {description}

Your job is to analyze this description carefully and identify:
1. What is clearly defined
2. What is missing or ambiguous
3. What questions you need answered before you can plan this project properly

Return ONLY valid JSON with no markdown:
{{
  "clarity_score": 0.0,
  "what_is_clear": ["item 1", "item 2"],
  "what_is_missing": ["item 1", "item 2"],
  "what_is_ambiguous": ["item 1", "item 2"],
  "identified_technologies": ["tech1", "tech2"],
  "identified_constraints": ["constraint1"],
  "estimated_complexity": "low|medium|high|very_high",
  "questions": [
    {{
      "id": "q1",
      "category": "scope|team|timeline|technology|budget|quality|constraints",
      "question": "specific question",
      "why_important": "why this matters for planning",
      "required": true
    }}
  ],
  "can_proceed_without_answers": false,
  "summary": "one sentence summary of what you understood"
}}

Rules:
- clarity_score is 0.0 to 1.0 (how complete the description is)
- Ask maximum 5 questions, prioritize the most critical ones
- required: true means the project cannot be planned without this answer
- can_proceed_without_answers: true only if clarity_score >= 0.8
- Return ONLY the JSON, nothing else"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


async def generate_tasks_with_context(
    project_name: str,
    description: str,
    answers: dict,
    team_skills: list[str] = None,
) -> dict:
    context_parts = []
    if answers.get("timeline"):
        context_parts.append(f"Timeline: {answers['timeline']}")
    if answers.get("team_size"):
        context_parts.append(f"Team size: {answers['team_size']}")
    if answers.get("tech_stack"):
        context_parts.append(f"Tech stack: {answers['tech_stack']}")
    if answers.get("must_haves"):
        context_parts.append(f"Must-haves: {answers['must_haves']}")
    if answers.get("nice_to_haves"):
        context_parts.append(f"Nice-to-haves: {answers['nice_to_haves']}")
    if answers.get("constraints"):
        context_parts.append(f"Constraints: {answers['constraints']}")
    if answers.get("definition_of_done"):
        context_parts.append(f"Definition of done: {answers['definition_of_done']}")
    if answers.get("budget"):
        context_parts.append(f"Budget: {answers['budget']}")

    for key, value in answers.items():
        if key not in ["timeline", "team_size", "tech_stack", "must_haves",
                       "nice_to_haves", "constraints", "definition_of_done", "budget"]:
            context_parts.append(f"{key}: {value}")

    context = "\n".join(context_parts)
    skills_context = f"Available team skills: {', '.join(team_skills)}" if team_skills else ""

    prompt = f"""You are an expert project manager. Create a detailed, accurate project plan.

Project: {project_name}
Description: {description}

Additional context from client:
{context}

{skills_context}

Return ONLY valid JSON with no markdown:
{{
  "summary": "one paragraph project summary",
  "total_estimated_hours": 0,
  "estimated_duration_weeks": 0,
  "risk_level": "low|medium|high|critical",
  "phases": ["phase1", "phase2"],
  "milestones": [
    {{
      "name": "milestone name",
      "description": "what this represents",
      "estimated_week": 1
    }}
  ],
  "tasks": [
    {{
      "id": "t1",
      "title": "Task title",
      "description": "Detailed description of what needs to be done",
      "priority": "low|medium|high|critical",
      "estimated_hours": 4,
      "required_skills": ["skill1"],
      "dependencies": [],
      "phase": "planning|development|testing|deployment",
      "milestone": "milestone name this contributes to",
      "acceptance_criteria": "how we know this task is done"
    }}
  ],
  "risks": [
    {{
      "risk": "description of risk",
      "severity": "low|medium|high|critical",
      "probability": "low|medium|high",
      "mitigation": "how to handle it"
    }}
  ],
  "assumptions": ["assumption 1", "assumption 2"]
}}

Rules:
- Break into tasks of 2-8 hours each
- priority must be one of: low, medium, high, critical
- phase must be one of: planning, development, testing, deployment
- Be specific — use the context provided to create accurate tasks
- Include at least 8 tasks
- Return ONLY the JSON, nothing else"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
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