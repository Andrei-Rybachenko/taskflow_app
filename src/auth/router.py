from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.auth.users import auth_backend, fastapi_users
from src.routers import current_active_user
from src.models.users import User
from src.auth.schemas import UserRead, UserCreate, UserUpdate
from src.schemas import MembershipRead

from src.services.users_service import UsersService
from src.dependencies import users_service, admin_required


auth_router = fastapi_users.get_auth_router(auth_backend)
register_router = fastapi_users.get_register_router(UserRead, UserCreate)
fastapi_users_router = fastapi_users.get_users_router(UserRead, UserUpdate)


users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("",
                  response_model=list[UserRead],
                  status_code=status.HTTP_200_OK)
async def get_users(
    service: Annotated[UsersService, Depends(users_service)],
    _: User = Depends(admin_required)
):
    """
    Ручка возвращает всех пользователей из базы.
    """
    users = await service.get_users()

    return users


@users_router.get(
    "/me/teams/{team_id}/members",
    response_model=list[MembershipRead],
    status_code=status.HTTP_200_OK,
)
async def get_users_team_members(
    team_id: int,
    service: Annotated[UsersService, Depends(users_service)],
    current_user: User = Depends(current_active_user)
):
    """
    Ручка возвращает участников команд, в которых состоит пользователь.
    """
    members = await service.get_user_teams_members(current_user.id, team_id)

    return members
