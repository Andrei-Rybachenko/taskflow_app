
from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from src.auth.users import auth_backend, get_user_manager, current_active_user
from src.dependencies import admin_required
from src.models import TeamORM, MembershipORM
from src.models.users import User
from src.auth.schemas import UserRead, UserCreate, UserUpdate
from src.database import get_async_session
from src.schemas import TeamRead, MembershipRead
from src.schemas.common_schemas import TeamShort

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

auth_router = fastapi_users.get_auth_router(auth_backend)
register_router = fastapi_users.get_register_router(UserRead, UserCreate)
fastapi_users_router = fastapi_users.get_users_router(UserRead, UserUpdate)


users_router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@users_router.get("/",
                  response_model=list[UserRead],
                  status_code=status.HTTP_200_OK)
async def get_users(db: AsyncSession = Depends(get_async_session)):
    """

    Ручка возвращает всех пользователей из базы.

    """

    stmt = select(User).order_by(User.id)

    result = await db.scalars(stmt)
    return result.all()


@users_router.get("/me/teams",
                  response_model=list[TeamShort],
                  status_code=status.HTTP_200_OK)
async def get_user_teams(
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)):

    """

    Ручка возвращает все команды, в которых состоит текущий пользователь.

    """

    stmt = (select(TeamORM)
            .join(TeamORM.memberships)
            .where(MembershipORM.user_id==current_user.id))

    result = await db.scalars(stmt)
    user_teams = result.all()

    return user_teams



@users_router.get("/{user_id}/teams",
                  response_model=list[TeamShort],
                  status_code=status.HTTP_200_OK)
async def get_user_teams(
        user_id: int,
        _: User = Depends(admin_required),
        db: AsyncSession = Depends(get_async_session)):

    """

    Админ-ручка возвращает все команды, в которых состоит пользователь.

    """

    stmt = (select(TeamORM)
            .join(TeamORM.memberships)
            .where(MembershipORM.user_id==user_id))

    result = await db.scalars(stmt)
    user_teams = result.all()

    return user_teams


@users_router.get("/me/teams/{team_id}/members",
                   response_model=list[MembershipRead],
                   status_code=status.HTTP_200_OK)

async def get_users_team_members(
        team_id: int,
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)):
    """

    Ручка возвращает участников команд, в которых состоит пользователь.

    """

    stmt = select(MembershipORM).where(MembershipORM.team_id==team_id,
                                       MembershipORM.user_id==current_user.id)
    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(403, detail="Вы не являетесь участником этой команды.")

    stmt = (select(MembershipORM)
    .where(MembershipORM.team_id==team_id)
    .options(joinedload(MembershipORM.user)))

    result = await db.scalars(stmt)
    team_members = result.all()

    return team_members