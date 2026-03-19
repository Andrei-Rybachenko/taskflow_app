from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import status

from src.models import User
from src.dependencies import admin_required, admin_or_manager_required, memberships_service

from src.schemas import MembershipCreate, MembershipRead, MembershipUpdate
from src.services.memberships_service import MembershipsService


memberships_router = APIRouter(prefix="/memberships", tags=["memberships"])


@memberships_router.post(
    "/create",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED
)
async def add_member(
    membership_create: MembershipCreate,
    service: Annotated[MembershipsService, Depends(memberships_service)],
    _: User = Depends(admin_required),

):
    """
    Ручка для добавления участника в команду.
    """
    membership = await service.add_member(membership_create)
    return membership


@memberships_router.delete(
    "/team/{team_id}/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_member(
    team_id: int,
    user_id: int,
    service: Annotated[MembershipsService, Depends(memberships_service)],
    _: User = Depends(admin_required)
):
    """
    Ручка для удаления участника из команды.
    """
    await service.delete(user_id, team_id)


@memberships_router.get(
    "/team/{team_id}/",
    response_model=list[MembershipRead],
    status_code=status.HTTP_200_OK,
)
async def get_team_members(
    team_id: int,
    service: Annotated[MembershipsService, Depends(memberships_service)],
    _: User = Depends(admin_or_manager_required)
):
    """
    Ручка возвращает всех участников команды.
    """
    members = await service.get_members(team_id)

    return members


@memberships_router.patch(
    "/team/{team_id}/{user_id}",
    response_model=MembershipRead,
    status_code=status.HTTP_200_OK,
)
async def change_role(
    team_id: int,
    user_id: int,
    membership_update: MembershipUpdate,
    service: Annotated[MembershipsService, Depends(memberships_service)],
    _: User = Depends(admin_required)
):
    """
    Ручка для изменения роли участника в команде.
    """
    updated_membership = await service.change_role(membership_update, user_id, team_id)

    return updated_membership