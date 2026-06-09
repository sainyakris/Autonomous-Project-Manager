import json
import re
from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)
CONFIDENCE_THRESHOLD = 0.75


async def run_decision_engine(project_state: dict) -> dict:
    prompt = f"""You are an autonomous AI project manager. Analyze this project state and decide what actions to take.

Project State:
{json.dumps(project_state, indent=2, default=str)}

For each issue you detect, propose a concrete action.

Return ONLY valid JSON with no markdown:
{{
  "observations": ["issue 1", "issue 2"],
  "decisions": [
    {{
      "id": "d1",
      "type": "reassign|reprioritize|deadline_adjust|flag_risk|escalate",
      "task_id": "task_id or null",
      "reasoning": "why this action is needed",
      "action": {{
        "description": "what to do in plain English",
        "from": "current state",
        "to": "proposed new state"
      }},
      "confidence": 0.0,
      "confidence_reasoning": "why this confidence level",
      "priority": "low|medium|high|critical"
    }}
  ],
  "overall_health": "green|yellow|red",
  "health_summary": "one sentence summary of project health"
}}

Confidence scoring guide:
- 0.9+: Routine, obvious action
- 0.75-0.9: Probable action
- 0.5-0.75: Uncertain — escalate to human
- <0.5: Too uncertain — always escalate

Return ONLY the JSON, nothing else"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    result = json.loads(raw)

    for decision in result.get("decisions", []):
        confidence = decision.get("confidence", 0.0)
        decision["will_act_autonomously"] = confidence >= CONFIDENCE_THRESHOLD
        decision["confidence_threshold"] = CONFIDENCE_THRESHOLD

    return result


async def build_project_state(project, tasks, team_members, recent_blockers) -> dict:
    return {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "progress": project.progress,
            "risk_level": project.risk_level,
            "status": str(project.status),
        },
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "status": str(t.status),
                "priority": str(t.priority),
                "estimated_hours": t.estimated_hours,
                "actual_hours": t.actual_hours,
                "delay_probability": t.delay_probability,
                "assignee_id": str(t.assignee_id) if t.assignee_id else None,
                "dependencies": t.dependencies or [],
            }
            for t in tasks
        ],
        "team": [
            {
                "id": str(m.id),
                "name": m.name,
                "skills": m.skills or [],
                "availability": m.availability,
                "performance_score": m.performance_score,
            }
            for m in team_members
        ],
        "recent_blockers": [
            {
                "task_id": str(b.task_id),
                "blocker": b.parsed_blocker,
                "sentiment": b.parsed_sentiment,
            }
            for b in recent_blockers
        ],
    }