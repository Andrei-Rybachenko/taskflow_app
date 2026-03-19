from fastapi import HTTPException
from starlette import status

from src.repositories.comments_repository import CommentsRepository
from src.repositories.tasks_repo import TasksRepository
from src.schemas import CommentCreate


class CommentsService:
    def __init__(
            self,
            comments_repo: CommentsRepository,
            tasks_repo: TasksRepository
    ):
        self.comments_repo = comments_repo
        self.tasks_repo = tasks_repo


    async def create_comment(self, comment: CommentCreate, author_id: int):
        task = await self.tasks_repo.get_task_by_id(comment.task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
            )

        new_comment = comment.model_dump()
        result = await self.comments_repo.add(new_comment, author_id)

        return result


    async def delete_comment(self, comment_id: int, author_id: int):
        comment_to_delete = await self.comments_repo.find_one(comment_id)

        if not comment_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Комментарий не найден."
            )

        if comment_to_delete.author_id != author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав на удаление комментария.",
            )

        await self.comments_repo.delete(comment_id)


    async def get_comments(self, task_id):
        task = await self.tasks_repo.get_task_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
            )

        comments = await self.comments_repo.get(task_id)

        if not comments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="У задачи нет комментариев."
            )

        return comments

