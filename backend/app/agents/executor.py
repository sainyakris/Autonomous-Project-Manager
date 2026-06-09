from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Task, TaskStatus, TaskPriority, AIDecision, DecisionType, DecisionStatus
from app.agents.decision_engine import CONFIDENCE_THRESHOLD
import uuid
import re as _re


def gen_uuid():
    return str(uuid.uuid4())


class Notification:
    _store: list = []

    @classmethod
    def send(cls, notification: dict):
        notification["id"] = gen_uuid()
        notification["timestamp"] = datetime.now(timezone.utc).isoformat()
        cls._store.append(notification)
        level = notification.get("level", "info").upper()
        print(f"\n🔔 [{level}] NOTIFICATION: {notification['title']}")
        print(f"   {notification['message']}\n")

    @classmethod
    def get_all(cls) -> list:
        return list(reversed(cls._store))

    @classmethod
    def clear(cls):
        cls._store = []


async def execute_decisions(
    decisions: list[dict],
    project_id: str,
    db: AsyncSession
) -> dict:
    executed = []
    escalated = []

    for decision in decisions:
        confidence = decision.get("confidence", 0.0)
        decision_type = decision.get("type", "flag_risk")
        task_id = decision.get("task_id")
        reasoning = decision.get("reasoning", "")
        action = decision.get("action", {})
        priority = decision.get("priority", "medium")

        ai_decision = AIDecision(
            project_id=project_id,
            task_id=task_id,
            decision_type=_map_decision_type(decision_type),
            confidence=confidence,
            confidence_threshold=CONFIDENCE_THRESHOLD,
            reasoning=reasoning,
            action_taken=action,
        )

        if confidence >= CONFIDENCE_THRESHOLD:
            await _execute_action(decision, db)
            ai_decision.status = DecisionStatus.EXECUTED

            Notification.send({
                "level": "priority" if priority in ["high", "critical"] else "info",
                "title": f"AI Action Taken — {decision_type.replace('_', ' ').title()}",
                "message": action.get("description", reasoning),
                "confidence": confidence,
                "autonomous": True,
                "project_id": project_id,
                "task_id": task_id,
            })
            executed.append(decision)
        else:
            ai_decision.status = DecisionStatus.ESCALATED

            Notification.send({
                "level": "warning",
                "title": f"⚠️ Human Review Required — {decision_type.replace('_', ' ').title()}",
                "message": f"{reasoning} (AI confidence: {int(confidence * 100)}% — below threshold)",
                "confidence": confidence,
                "autonomous": False,
                "project_id": project_id,
                "task_id": task_id,
            })
            escalated.append(decision)

        db.add(ai_decision)

    await db.flush()

    return {
        "executed": len(executed),
        "escalated": len(escalated),
        "total": len(decisions),
        "autonomy_rate": round(len(executed) / len(decisions), 2) if decisions else 0.0,
        "executed_decisions": executed,
        "escalated_decisions": escalated,
    }


async def _execute_action(decision: dict, db: AsyncSession):
    decision_type = decision.get("type")
    task_id = decision.get("task_id")

    if not task_id:
        return

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return

    action = decision.get("action", {})
    to_state = action.get("to", "")

    if decision_type == "reprioritize":
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL,
        }
        new_priority = priority_map.get(to_state.lower())
        if new_priority:
            task.priority = new_priority

    elif decision_type == "reassign":
        uuid_pattern = _re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        )
        if to_state and uuid_pattern.match(to_state.lower()):
            task.assignee_id = to_state

    elif decision_type == "flag_risk":
        task.delay_probability = min(task.delay_probability + 0.3, 1.0)

    elif decision_type == "escalate":
        task.status = TaskStatus.BLOCKED


def _map_decision_type(dt: str) -> DecisionType:
    mapping = {
        "reassign": DecisionType.REASSIGN,
        "reprioritize": DecisionType.REPRIORITIZE,
        "deadline_adjust": DecisionType.DEADLINE_ADJUST,
        "flag_risk": DecisionType.FLAG_RISK,
        "escalate": DecisionType.ESCALATE,
    }
    return mapping.get(dt, DecisionType.FLAG_RISK)