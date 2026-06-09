from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.models import Task, TaskUpdate, User
from app.schemas.schemas import UpdateSubmit, UpdateOut
from app.agents.ai_agent import parse_team_update
from app.api.routes.projects import get_current_user
from typing import List

router = APIRouter(prefix="/updates", tags=["Updates"])


@router.post("/", response_model=UpdateOut)
async def submit_update(
    data: UpdateSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Task).where(Task.id == data.task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await db.execute(
        select(TaskUpdate)
        .where(TaskUpdate.task_id == data.task_id)
        .order_by(TaskUpdate.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    current_progress = latest.parsed_progress or 0.0 if latest else 0.0

    try:
        parsed = await parse_team_update(
            raw_text=data.text,
            task_title=task.title,
            current_progress=current_progress,
        )
    except Exception as e:
        print(f"Update parsing failed: {e}")
        parsed = {}

    update = TaskUpdate(
        task_id=data.task_id,
        author_id=current_user.id,
        raw_text=data.text,
        parsed_progress=parsed.get("progress"),
        parsed_blocker=parsed.get("blocker"),
        parsed_sentiment=parsed.get("sentiment"),
    )
    db.add(update)
    await db.flush()
    await db.refresh(update)
    return update


@router.get("/task/{task_id}", response_model=List[UpdateOut])
async def get_task_updates(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TaskUpdate)
        .where(TaskUpdate.task_id == task_id)
        .order_by(TaskUpdate.created_at.desc())
    )
    return result.scalars().all()