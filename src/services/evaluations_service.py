from fastapi import HTTPException
from starlette import status

from src.repositories.evaluations_repo import EvaluationsRepository, EvaluationReader, EvaluationWriter

from src.repositories.tasks_repo import TasksRepository, TaskReader
from src.schemas import EvaluationCreate


class EvaluationsService:
    def __init__(
            self,
            evaluation_reader: EvaluationReader,
            evaluation_writer: EvaluationWriter,
            task_reader: TaskReader
    ):
        self.evaluation_reader = evaluation_reader
        self.evaluation_writer = evaluation_writer
        self.task_reader = task_reader


    async def create(
            self,
            score: EvaluationCreate,
            task_id: int,
            reviewer_id: int,
            team_id: int,
    ):
        task = await self.task_reader.get_task_by_id(task_id)

        if not task or task.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена"
            )

        if not task.executor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Задача еще не назначена исполнителю",
            )

        existing = await self.evaluation_reader.get_evaluation_by_task_id(task_id)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Оценка уже выставлена.",
            )

        score_data = score.model_dump()
        if score_data.get("employee_id") != task.executor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Исполнитель в запросе должен совпадать с исполнителем задачи.",
            )
        try:
            task_score = await self.evaluation_writer.add(score_data, task_id, reviewer_id)
        except Exception:
            raise

        return task_score


    async def get_evaluation(self, task_id):
        task = await self.task_reader.get_task_by_id(task_id)

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

        score = await self.evaluation_reader.get_evaluation_by_task_id(task_id)

        return score
