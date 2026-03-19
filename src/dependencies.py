from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import select
from starlette import status

from src.repositories.comments_repository import CommentsRepository
from src.repositories.evaluations_repo import EvaluationsRepository
from src.repositories.meetings_repo import MeetingsRepository
from src.repositories.membership_repo import MembershipsRepository
from src.repositories.tasks_repo import TasksRepository
from src.repositories.teams_repo import TeamsRepository
from src.repositories.users_repo import UsersRepository
from src.routers import current_active_user
from src.database import get_async_session
from src.enums import Role
from src.models import MembershipORM
from src.services.comments_service import CommentsService
from src.services.evaluations_service import EvaluationsService
from src.services.meetings_service import MeetingsService
from src.services.memberships_service import MembershipsService
from src.services.tasks_service import TasksService
from src.services.teams_service import TeamsService


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.models.users import User


async def admin_required(user: "User" = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав.",
        )
    return user



def tasks_service(
    db: "AsyncSession" = Depends(get_async_session)
):
    tasks_repo = TasksRepository(db)
    teams_repo = TeamsRepository(db)
    memberships_repo = MembershipsRepository(db)

    return TasksService(tasks_repo, teams_repo, memberships_repo)


def teams_service(
    db: "AsyncSession" = Depends(get_async_session)
):
    teams_repo = TeamsRepository(db)

    return TeamsService(teams_repo)


def memberships_service(
    db: "AsyncSession" = Depends(get_async_session)
):
    memberships_repo = MembershipsRepository(db)
    tasks_repo = TasksRepository(db)
    teams_repo = TeamsRepository(db)
    users_repo = UsersRepository(db)

    return MembershipsService(memberships_repo, tasks_repo, teams_repo, users_repo)

#
# def users_service(
#     db: "AsyncSession" = Depends(get_async_session)
# ):
#     users_repo = UsersRepository(db)
#
#     return UsersService(users_repo)


def meetings_service(
    db: "AsyncSession" = Depends(get_async_session)
):
    meetings_repo = MeetingsRepository(db)

    return MeetingsService(meetings_repo)


def evaluations_service(
    db: "AsyncSession" = Depends(get_async_session)
):
    evaluations_repo = EvaluationsRepository(db)
    tasks_repo = TasksRepository(db)

    return EvaluationsService(evaluations_repo, tasks_repo)


def comments_service(
    db: "AsyncSession" = Depends(get_async_session)
):
    comments_repo = CommentsRepository(db)
    tasks_repo = TasksRepository(db)

    return CommentsService(comments_repo, tasks_repo)


async def manager_required(
    team_id: int,
    service: Annotated[MembershipsService, Depends(memberships_service)],
    current_user: "User" = Depends(current_active_user)
):

    membership = await service.get(current_user.id, team_id)

    if not membership or membership.role not in [Role.MANAGER,
                                                 Role.TEAM_ADMIN]:
        raise HTTPException(403)

    return current_user


async def admin_or_manager_required(
    team_id: int | None,
    service: Annotated[MembershipsService, Depends(memberships_service)],
    current_user: "User" = Depends(current_active_user)
):
    if current_user.is_superuser:
        return current_user

    if team_id is not None:
        membership = await service.get(current_user.id, team_id)

        if membership and membership.role in [Role.MANAGER,
                                              Role.TEAM_ADMIN]:
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
    )


async def team_member_required(
    team_id: int,
    service: Annotated[MembershipsService, Depends(memberships_service)],
    current_user: "User" = Depends(current_active_user)
):
    if current_user.is_superuser:
        return current_user

    membership = await service.get(current_user.id, team_id)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    return current_user
