from fastapi import HTTPException
from starlette import status

from src.repositories.evaluations_repo import EvaluationsRepository

from src.repositories.tasks_repo import TasksRepository
from src.schemas import EvaluationCreate


class EvaluationsService:
    def __init__(
            self,
            evaluations_repo: EvaluationsRepository,
            tasks_repo: TasksRepository
    ):
        self.evaluations_repo = evaluations_repo
        self.tasks_repo = tasks_repo

    async def create(
            self,
            score: EvaluationCreate,
            task_id: int,
            reviewer_id: int
    ):
        task = await self.tasks_repo.find_one(task_id)

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

        existing = await self.evaluations_repo.get_evaluation_by_task_id(task_id)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Оценка уже выставлена.",
            )

        score = score.model_dump()
        task_score = await self.evaluations_repo.add(score, task_id, reviewer_id)

        return task_score


    async def get_evaluation(self, task_id):
        task = await self.tasks_repo.get_task_by_id(task_id)

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

        score = await self.evaluations_repo.get_evaluation_by_task_id(task_id)

        return score
