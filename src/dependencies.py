from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException
from sqlalchemy import select
from starlette import status

from src.routers import current_active_user
from src.database import get_async_session
from src.enums import Role
from src.models import MembershipORM

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.models.users import User


async def admin_required(user: "User" = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have a permission to create a team.",
        )
    return user


async def manager_required(
    team_id: int,
    current_user: "User" = Depends(current_active_user),
    db: "AsyncSession" = Depends(get_async_session),
):

    stmt = select(MembershipORM).where(
        MembershipORM.team_id == team_id,
        MembershipORM.user_id == current_user.id,
    )

    membership = await db.scalar(stmt)

    if not membership or membership.role not in [Role.MANAGER,
                                                 Role.TEAM_ADMIN]:
        raise HTTPException(403)

    return current_user


async def admin_or_manager_required(
    team_id: int | None,
    current_user: "User" = Depends(current_active_user),
    db: "AsyncSession" = Depends(get_async_session),
):

    if current_user.is_superuser:
        return current_user

    if team_id is not None:
        stmt = select(MembershipORM).where(
            MembershipORM.user_id == current_user.id,
            MembershipORM.team_id == team_id
        )

        membership = await db.scalar(stmt)

        if membership and membership.role in ["MANAGER", "TEAM_ADMIN"]:
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
    )


async def team_member_required(
    team_id: int,
    current_user: "User" = Depends(current_active_user),
    db: "AsyncSession" = Depends(get_async_session),
):

    if current_user.is_superuser:
        return current_user

    stmt = select(MembershipORM).where(
        MembershipORM.team_id == team_id,
        MembershipORM.user_id == current_user.id
    )

    membership = await db.scalar(stmt)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )

    return current_user
