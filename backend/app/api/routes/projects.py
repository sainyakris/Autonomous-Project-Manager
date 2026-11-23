import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.models import Project, Task, TaskPriority, User, new_id, task_dependencies
from app.schemas.projects import (
    AnalyzeRequest, AnalyzeResponse, ProjectCreate, ProjectDetail, ProjectOut, TaskOut,
)
from app.services.intake import READY_THRESHOLD, analyze_brief, generate_plan
from app.services.llm import LLMError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["Projects"])


async def build_detail(db: AsyncSession, project: Project) -> ProjectDetail:
    tasks = (
        await db.scalars(
            select(Task).where(Task.project_id == project.id).order_by(Task.position)
        )
    ).all()

    deps: dict[str, list[str]] = defaultdict(list)
    if tasks:
        rows = await db.execute(
            select(task_dependencies.c.task_id, task_dependencies.c.depends_on_id).where(
                task_dependencies.c.task_id.in_([t.id for t in tasks])
            )
        )
        for task_id, depends_on_id in rows:
            deps[task_id].append(depends_on_id)

    task_out = [
        TaskOut.model_validate(t).model_copy(update={"depends_on": deps.get(t.id, [])})
        for t in tasks
    ]
    return ProjectDetail(**ProjectOut.model_validate(project).model_dump(), tasks=task_out)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(data: AnalyzeRequest, user: User = Depends(get_current_user)):
    try:
        analysis = await analyze_brief(data.name, data.description)
    except LLMError:
        logger.exception("analysis failed")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The AI service could not analyze this brief. Try again.")
    return AnalyzeResponse(
        **analysis.model_dump(), ready=analysis.clarity_score >= READY_THRESHOLD
    )


@router.post("", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Generate FIRST. If the AI fails we save nothing, so no empty projects.
    try:
        plan = await generate_plan(data.name, data.description, data.answers)
    except LLMError:
        logger.exception("plan generation failed")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The AI service could not produce a valid plan. Try again.")

    project = Project(
        name=data.name,
        description=data.description,
        owner_id=user.id,
        summary=plan.summary,
        risk_level=plan.risk_level,
        context=data.answers or None,
    )
    db.add(project)
    await db.flush()  # assigns project.id

    # Temporary plan keys ("t1") -> real task ids
    tasks_by_key: dict[str, Task] = {}
    for position, pt in enumerate(plan.tasks):
        task = Task(
            id=new_id(),
            project_id=project.id,
            title=pt.title,
            description=pt.description,
            priority=TaskPriority(pt.priority),
            estimated_hours=pt.estimated_hours,
            position=position,
        )
        tasks_by_key[pt.key] = task
        db.add(task)
    await db.flush()  # tasks must exist before links can reference them

    links = [
        {"task_id": tasks_by_key[pt.key].id, "depends_on_id": tasks_by_key[dep].id}
        for pt in plan.tasks
        for dep in pt.depends_on
    ]
    if links:
        await db.execute(insert(task_dependencies), links)

    await db.commit()  # project, tasks and links are saved together or not at all
    await db.refresh(project)
    return await build_detail(db, project)


@router.get("", response_model=list[ProjectOut])
async def list_projects(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.scalars(
        select(Project).where(Project.owner_id == user.id).order_by(Project.created_at.desc())
    )
    return result.all()


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.owner_id == user.id)
    )
    if project is None:  # 404 (not 403) so users can't probe for other people's ids
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return await build_detail(db, project)