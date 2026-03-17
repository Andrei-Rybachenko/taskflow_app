from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from sqlalchemy.orm import selectinload

from src.models import User, MembershipORM
from src.database import get_async_session
from src.dependencies import admin_required, admin_or_manager_required

from src.models.teams import TeamORM
from src.schemas.common_schemas import TeamShort

from src.schemas.teams import TeamRead, TeamCreate

teams_router = APIRouter(prefix="/teams", tags=["teams"])


@teams_router.post(
    "/create", response_model=TeamShort, status_code=status.HTTP_201_CREATED
)
async def create_team(
    team: TeamCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_async_session),
):
    """

    Ручка для создания команды.

    """

    new_team = TeamORM(**team.model_dump(), owner_id=current_user.id)
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)

    return new_team


@teams_router.get(
    "/all_teams",
    response_model=list[TeamShort],
    status_code=status.HTTP_200_OK
)
async def get_teams(
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_async_session)
):
    """

    Ручка возвращает все команды.

    """

    stmt = select(TeamORM).order_by(TeamORM.id)
    result = await db.scalars(stmt)
    teams = result.all()

    return teams


@teams_router.get("/{team_id}",
                  response_model=TeamRead,
                  status_code=status.HTTP_200_OK)
async def get_team_by_id(
    team_id: int,
    _: User = Depends(admin_or_manager_required),
    db: AsyncSession = Depends(get_async_session),
):
    """

    Ручка возвращает команду по id.

    """

    stmt = (
        select(TeamORM)
        .where(TeamORM.id == team_id)
        .options(
            selectinload(TeamORM.memberships),
            selectinload(TeamORM.meetings),
            selectinload(TeamORM.tasks),
        )
    )

    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой команды не существует"
        )

    return team


@teams_router.get(
    "/user/{user_id}",
    response_model=list[TeamShort],
    status_code=status.HTTP_200_OK
)
async def get_user_teams(
    user_id: int,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_async_session),
):
    """

    Админ-ручка возвращает все команды, в которых состоит пользователь.

    """

    stmt = (
        select(TeamORM)
        .join(TeamORM.memberships)
        .where(MembershipORM.user_id == user_id)
    )

    result = await db.scalars(stmt)
    user_teams = result.all()

    return user_teams
