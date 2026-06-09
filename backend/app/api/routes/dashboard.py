from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import Project, Task, TaskUpdate, TaskStatus, ClientReport
from app.agents.ai_agent import generate_client_report
from app.api.routes.projects import get_current_user
from app.models.models import User
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/{project_id}")
async def get_project_dashboard(
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

    total = len(tasks)
    done = len([t for t in tasks if t.status == TaskStatus.DONE])
    in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
    blocked = len([t for t in tasks if t.status == TaskStatus.BLOCKED])
    todo = len([t for t in tasks if t.status == TaskStatus.TODO])

    result = await db.execute(
        select(TaskUpdate)
        .where(TaskUpdate.parsed_blocker != None)
        .order_by(TaskUpdate.created_at.desc())
        .limit(5)
    )
    recent_blockers = result.scalars().all()

    progress = round(done / total, 2) if total > 0 else 0.0

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "risk_level": project.risk_level,
            "progress": progress,
        },
        "task_summary": {
            "total": total,
            "done": done,
            "in_progress": in_progress,
            "blocked": blocked,
            "todo": todo,
        },
        "blockers": [
            {
                "blocker": u.parsed_blocker,
                "sentiment": u.parsed_sentiment,
                "reported_at": u.created_at,
            }
            for u in recent_blockers
        ],
        "health": "red" if blocked > 0 else "yellow" if in_progress > 0 else "green",
    }


class ReportRequest(BaseModel):
    project_id: str


@router.post("/report/generate")
async def generate_report(
    data: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Project).where(
            Project.id == data.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Task).where(Task.project_id == data.project_id)
    )
    tasks = result.scalars().all()

    completed = [t.title for t in tasks if t.status == TaskStatus.DONE]
    upcoming = [t.title for t in tasks if t.status == TaskStatus.TODO][:5]
    total = len(tasks)
    done = len(completed)
    progress = round(done / total, 2) if total > 0 else 0.0

    result = await db.execute(
        select(TaskUpdate)
        .where(TaskUpdate.parsed_blocker != None)
        .order_by(TaskUpdate.created_at.desc())
        .limit(3)
    )
    blocker_updates = result.scalars().all()
    risks = [u.parsed_blocker for u in blocker_updates]

    try:
        report_data = await generate_client_report(
            project_name=project.name,
            progress=progress,
            completed_tasks=completed,
            upcoming_tasks=upcoming,
            risks=risks if risks else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

    report = ClientReport(
        project_id=data.project_id,
        title=report_data.get("subject", f"{project.name} Status Report"),
        content=report_data.get("report", ""),
    )
    db.add(report)
    await db.flush()

    return {
        "subject": report_data.get("subject"),
        "report": report_data.get("report"),
        "tone": report_data.get("tone"),
        "key_wins": report_data.get("key_wins", []),
        "next_milestone": report_data.get("next_milestone"),
    }