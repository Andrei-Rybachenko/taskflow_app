from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import status

from src.models import User
from src.dependencies import manager_required, admin_or_manager_required, evaluations_service

from src.schemas import EvaluationRead, EvaluationCreate
from src.services.evaluations_service import EvaluationsService


evaluations_router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@evaluations_router.post(
    "/task/{task_id}",
    response_model=EvaluationRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_score_for_task(
    task_id: int,
    score: EvaluationCreate,
    service: Annotated[EvaluationsService, Depends(evaluations_service)],
    current_user: User = Depends(manager_required)
):
    task_score = await service.create(score, task_id, current_user.id)

    return task_score


@evaluations_router.get(
    "/task/{task_id}",
    response_model=EvaluationRead,
    status_code=status.HTTP_200_OK
)
async def get_score_for_task_by_id(
    task_id: int,
    service: Annotated[EvaluationsService, Depends(evaluations_service)],
    _: User = Depends(admin_or_manager_required)
):
    score = await service.get_evaluation(task_id)

    return score

