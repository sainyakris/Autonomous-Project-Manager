from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import Project, Task, User, TaskUpdate
from app.agents.decision_engine import run_decision_engine, build_project_state
from app.agents.executor import execute_decisions, Notification
from app.api.routes.projects import get_current_user

router = APIRouter(prefix="/autonomy", tags=["Autonomy"])


@router.post("/run/{project_id}")
async def run_autonomy_cycle(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = result.scalars().all()

    result = await db.execute(select(User))
    team_members = result.scalars().all()

    result = await db.execute(
        select(TaskUpdate)
        .where(TaskUpdate.parsed_blocker != None)
        .order_by(TaskUpdate.created_at.desc())
        .limit(10)
    )
    recent_blockers = result.scalars().all()

    state = await build_project_state(project, tasks, team_members, recent_blockers)
    engine_result = await run_decision_engine(state)
    decisions = engine_result.get("decisions", [])
    execution_result = await execute_decisions(decisions, project_id, db)

    if execution_result["total"] > 0:
        project.autonomy_score = execution_result["autonomy_rate"]

    await db.flush()

    return {
        "project_id": project_id,
        "observations": engine_result.get("observations", []),
        "overall_health": engine_result.get("overall_health"),
        "health_summary": engine_result.get("health_summary"),
        "decisions_made": execution_result["total"],
        "executed_autonomously": execution_result["executed"],
        "escalated_to_human": execution_result["escalated"],
        "autonomy_rate": execution_result["autonomy_rate"],
        "executed_decisions": execution_result["executed_decisions"],
        "escalated_decisions": execution_result["escalated_decisions"],
    }


@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
):
    return {
        "notifications": Notification.get_all(),
        "total": len(Notification.get_all()),
    }


@router.delete("/notifications")
async def clear_notifications(
    current_user: User = Depends(get_current_user),
):
    Notification.clear()
    return {"message": "Notifications cleared"}