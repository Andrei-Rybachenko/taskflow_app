from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import status

from src.models import User
from src.dependencies import admin_required, admin_or_manager_required, teams_service

from src.schemas.common_schemas import TeamShort

from src.schemas.teams import TeamRead, TeamCreate
from src.services.teams_service import TeamsService


teams_router = APIRouter(prefix="/teams", tags=["teams"])


@teams_router.post(
    "/create",
    response_model=TeamShort,
    status_code=status.HTTP_201_CREATED
)
async def create_team(
    team: TeamCreate,
    service: Annotated[TeamsService, Depends(teams_service)],
    current_user: User = Depends(admin_required)
):
    """
    Ручка для создания команды.
    """
    new_team = await service.create(team, current_user.id)

    return new_team


@teams_router.get(
    "/all_teams",
    response_model=list[TeamShort],
    status_code=status.HTTP_200_OK
)
async def get_teams(
    service: Annotated[TeamsService, Depends(teams_service)],
    _: User = Depends(admin_required)
):
    """
    Ручка возвращает все команды.
    """
    teams = await service.get_teams()

    return teams


@teams_router.get("/{team_id}",
                  response_model=TeamRead,
                  status_code=status.HTTP_200_OK)
async def get_team_by_id(
    team_id: int,
    service: Annotated[TeamsService, Depends(teams_service)],
    _: User = Depends(admin_or_manager_required)
):
    """
    Ручка возвращает команду по id.
    """

    team = await service.get_team(team_id)

    return team


@teams_router.get(
    "/user/{user_id}",
    response_model=list[TeamShort],
    status_code=status.HTTP_200_OK
)
async def get_user_teams(
    user_id: int,
    service: Annotated[TeamsService, Depends(teams_service)],
    _: User = Depends(admin_required)
):
    """
    Админ-ручка возвращает все команды, в которых состоит пользователь.
    """
    user_teams = await service.get_user_teams(user_id)

    return user_teams
