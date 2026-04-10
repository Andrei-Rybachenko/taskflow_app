from fastapi import HTTPException
from starlette import status

from src.repositories.comments_repository import CommentsRepository, CommentReader, CommentWriter
from src.repositories.tasks_repo import TasksRepository, TaskReader
from src.schemas import CommentCreate


class CommentsService:
    def __init__(
            self,
            comment_reader: CommentReader,
            comment_writer: CommentWriter,
            task_reader: TaskReader
    ):
        self.comment_reader = comment_reader
        self.comment_writer = comment_writer
        self.task_reader = task_reader


    async def create_comment(
        self, comment: CommentCreate, author_id: int, team_id: int
    ):
        task = await self.task_reader.get_task_by_id(comment.task_id)

        if not task or task.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
            )

        try:
            new_comment = comment.model_dump()
            result = await self.comment_writer.add(new_comment, author_id)
            return result
        except Exception:
            raise


    async def delete_comment(
        self, comment_id: int, author_id: int, task_id: int
    ):
        comment_to_delete = await self.comment_reader.find_one(comment_id)

        if not comment_to_delete or comment_to_delete.task_id != task_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Комментарий не найден."
            )

        if comment_to_delete.author_id != author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет прав на удаление комментария.",
            )

        try:
            await self.comment_writer.delete(comment_id)
        except Exception:
            raise


    async def get_comments(self, task_id: int, team_id: int):
        task = await self.task_reader.get_task_by_id(task_id)

        if not task or task.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
            )

        comments = await self.comment_reader.get_by_task_id(task_id)

        return comments or []

