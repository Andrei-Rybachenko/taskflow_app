from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from src.models import User, TaskORM
from src.database import get_async_session
from src.dependencies import team_member_required
from src.models.comments import CommentORM

from src.schemas import CommentRead, CommentCreate


comments_router = APIRouter(
    prefix="/comments",
    tags=["comments"]
)


@comments_router.post('/task/{task_id}',
                   response_model=CommentRead,
                   status_code=status.HTTP_201_CREATED)
async def add_comment_to_task(
        team_id: int,
        task_id: int,
        comment: CommentCreate,
        current_user: User = Depends(team_member_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(TaskORM)
            .where(TaskORM.id==task_id,
                   TaskORM.team_id==team_id
                   ))
    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    new_comment = CommentORM(**comment.model_dump(),
                             task_id=task_id,
                             author_id=current_user.id)

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return new_comment


@comments_router.get('/task/{task_id}',
                   response_model=list[CommentRead],
                   status_code=status.HTTP_200_OK)
async def get_comments_for_task(
        team_id: int,
        task_id: int,
        _: User = Depends(team_member_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(TaskORM)
            .where(TaskORM.id==task_id,
                   TaskORM.team_id==team_id)
            .options(joinedload(TaskORM.comments)))

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    return task.comments


@comments_router.delete('/task/{task_id}/{comment_id}',
                  status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_by_id(
        team_id: int,
        task_id: int,
        comment_id: int,
        current_user: User = Depends(team_member_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(CommentORM)
            .join(TaskORM, TaskORM.id==CommentORM.task_id)
            .where(CommentORM.task_id==task_id,
                   CommentORM.id==comment_id,
                   TaskORM.team_id==team_id))

    comment = await db.scalar(stmt)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комментарий не найден."
        )

    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на удаление комментария."
        )

    await db.delete(comment)
    await db.commit()