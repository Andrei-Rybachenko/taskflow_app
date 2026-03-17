from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from starlette import status

from src.models import User, TaskORM
from src.database import get_async_session
from src.dependencies import manager_required, admin_or_manager_required
from src.models.evaluations import EvaluationORM

from src.schemas import EvaluationRead, EvaluationCreate

evaluations_router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@evaluations_router.post(
    "/task/{task_id}",
    response_model=EvaluationRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_score_for_task(
    team_id: int,
    task_id: int,
    score: EvaluationCreate,
    _: User = Depends(manager_required),
    db: AsyncSession = Depends(get_async_session),
):

    stmt = select(TaskORM).where(TaskORM.id == task_id,
                                 TaskORM.team_id == team_id)

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    if not task.executor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Задача еще не назначена исполнителю",
        )

    stmt = select(EvaluationORM).where(EvaluationORM.task_id == task_id)
    existing = await db.scalar(stmt)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оценка для задачи уже выставлена.",
        )

    task_score = EvaluationORM(
        **score.model_dump(),
        task_id=task_id,
        employee_id=task.executor_id
    )

    db.add(task_score)
    await db.commit()
    await db.refresh(task_score)

    return task_score


@evaluations_router.get(
    "/task/{task_id}",
    response_model=EvaluationRead,
    status_code=status.HTTP_200_OK
)
async def get_scores_for_task_by_id(
    team_id: int,
    task_id: int,
    _: User = Depends(admin_or_manager_required),
    db: AsyncSession = Depends(get_async_session),
):

    stmt = (
        select(TaskORM)
        .where(TaskORM.id == task_id, TaskORM.team_id == team_id)
        .options(joinedload(TaskORM.evaluation))
    )

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    if not task.evaluation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оценка для задачи еще не выставлена.",
        )
    return task.evaluation
