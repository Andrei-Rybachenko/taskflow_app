from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.models import User
from src.dependencies import team_member_required, comments_service

from src.schemas import CommentRead, CommentCreate
from src.schemas.comments import CommentContentBody
from src.services.comments_service import CommentsService


comments_router = APIRouter(prefix="/comments", tags=["Комментарии"])


@comments_router.post(
    "/task/{task_id}",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED
)
async def add_comment_to_task(
    task_id: int,
    team_id: int,
    body: CommentContentBody,
    service: Annotated[CommentsService, Depends(comments_service)],
    current_user: User = Depends(team_member_required),
):
    comment = CommentCreate(task_id=task_id, content=body.content)
    new_comment = await service.create_comment(comment, current_user.id, team_id)

    return new_comment



@comments_router.get(
    "/task/{task_id}",
    response_model=list[CommentRead],
    status_code=status.HTTP_200_OK
)
async def get_comments_for_task(
    task_id: int,
    team_id: int,
    service: Annotated[CommentsService, Depends(comments_service)],
    _: User = Depends(team_member_required),
):
    comments = await service.get_comments(task_id, team_id)

    return comments


@comments_router.delete(
    "/task/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment_by_id(
    task_id: int,
    comment_id: int,
    team_id: int,
    service: Annotated[CommentsService, Depends(comments_service)],
    current_user: User = Depends(team_member_required),
):
    await service.delete_comment(comment_id, current_user.id, task_id)
