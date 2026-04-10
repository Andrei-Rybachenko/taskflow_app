from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException
from starlette import status

from src.repositories.comments_repository import CommentsRepository, CommentReader, CommentWriter
from src.repositories.evaluations_repo import EvaluationsRepository, EvaluationReader, EvaluationWriter
from src.repositories.meetings_repo import MeetingsRepository, MeetingReader, MeetingWriter
from src.repositories.membership_repo import MembershipsRepository, MembershipReader, MembershipWriter
from src.repositories.tasks_repo import TasksRepository, TaskReader, TaskWriter
from src.repositories.teams_repo import TeamsRepository, TeamReader, TeamWriter
from src.repositories.users_repo import UsersRepository, UserReader, UserWriter
from src.routers import current_active_user
from src.database import get_async_session
from src.enums import Role
from src.services.comments_service import CommentsService
from src.services.evaluations_service import EvaluationsService
from src.services.meetings_service import MeetingsService
from src.services.memberships_service import MembershipsService
from src.services.tasks_service import TasksService
from src.services.teams_service import TeamsService
from src.services.users_service import UsersService
from src.schemas.tasks import TaskCreate
from src.services.tasks_service import TasksService

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



def get_tasks_repo(
    db: "AsyncSession" = Depends(get_async_session)
) -> TasksRepository:
    return TasksRepository(db)


def get_teams_repo(
    db: "AsyncSession" = Depends(get_async_session)
) -> TeamsRepository:
    return TeamsRepository(db)


def get_memberships_repo(
    db: "AsyncSession" = Depends(get_async_session)
) -> MembershipsRepository:
    return MembershipsRepository(db)


def get_users_repo(
    db: "AsyncSession" = Depends(get_async_session)
) -> UsersRepository:
    return UsersRepository(db)


def get_meetings_repo(
    db: "AsyncSession" = Depends(get_async_session)
) -> MeetingsRepository:
    return MeetingsRepository(db)


def get_evaluations_repo(
    db: "AsyncSession" = Depends(get_async_session)
) -> EvaluationsRepository:
    return EvaluationsRepository(db)


def get_comments_repo(
    db: "AsyncSession" = Depends(get_async_session)
) -> CommentsRepository:
    return CommentsRepository(db)



def tasks_service(
    task_reader: TaskReader = Depends(get_tasks_repo),
    task_writer: TaskWriter = Depends(get_tasks_repo),
    team_reader: TeamReader = Depends(get_teams_repo),
    membership_reader: MembershipReader = Depends(get_memberships_repo)
):
    return TasksService(
        task_reader=task_reader,
        task_writer=task_writer,
        team_reader=team_reader,
        membership_reader=membership_reader
    )


def teams_service(
    team_reader: TeamReader = Depends(get_teams_repo),
    team_writer: TeamWriter = Depends(get_teams_repo)
):

    return TeamsService(
        team_reader=team_reader,
        team_writer=team_writer
    )


def memberships_service(
    membership_reader: MembershipReader = Depends(get_memberships_repo),
    membership_writer: MembershipWriter = Depends(get_memberships_repo),
    team_reader: TeamReader = Depends(get_teams_repo),
    user_reader: UserReader = Depends(get_users_repo)
):
    return MembershipsService(
        membership_reader=membership_reader,
        membership_writer=membership_writer,
        team_reader=team_reader,
        user_reader=user_reader
    )


def users_service(
    user_reader: UserReader = Depends(get_users_repo),
    user_writer: UserWriter = Depends(get_users_repo),
    membership_reader: MembershipReader = Depends(get_memberships_repo),
):
    return UsersService(
        user_reader=user_reader,
        user_writer=user_writer,
        membership_reader=membership_reader)


def meetings_service(
    meeting_reader: MeetingReader = Depends(get_meetings_repo),
    meeting_writer: MeetingWriter = Depends(get_meetings_repo)
):
    return MeetingsService(
        meeting_reader=meeting_reader,
        meeting_writer=meeting_writer
    )


def evaluations_service(
    evaluation_reader: EvaluationReader = Depends(get_evaluations_repo),
    evaluation_writer: EvaluationWriter = Depends(get_evaluations_repo),
    task_reader: TaskReader = Depends(get_tasks_repo)
):
    return EvaluationsService(
        evaluation_reader=evaluation_reader,
        evaluation_writer=evaluation_writer,
        task_reader=task_reader
    )


def comments_service(
    comment_reader: CommentReader = Depends(get_comments_repo),
    comment_writer: CommentWriter = Depends(get_comments_repo),
    task_reader: TaskReader = Depends(get_tasks_repo)
):
    return CommentsService(
        comment_reader=comment_reader,
        comment_writer=comment_writer,
        task_reader=task_reader
    )


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
    current_user: "User" = Depends(current_active_user),
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


async def admin_or_manager_required_from_task_create(
    task: TaskCreate,
    service: Annotated[MembershipsService, Depends(memberships_service)],
    current_user: "User" = Depends(current_active_user),
):
    """Для POST /tasks/create — team_id берётся из тела запроса."""
    return await admin_or_manager_required(task.team_id, service, current_user)


async def admin_or_manager_for_existing_task(
    task_id: int,
    tasks: Annotated[TasksService, Depends(tasks_service)],
    service: Annotated[MembershipsService, Depends(memberships_service)],
    current_user: "User" = Depends(current_active_user),
):
    """Проверка прав менеджера/админа команды по team_id существующей задачи."""
    task = await tasks.get_task_or_404(task_id)
    tid = task.team_id
    return await admin_or_manager_required(tid, service, current_user)


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
