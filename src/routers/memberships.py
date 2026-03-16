from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from src.enums import Role
from src.models import User, MembershipORM
from src.database import get_async_session
from src.dependencies import admin_required, admin_or_manager_required

from src.models.teams import TeamORM
from src.schemas import MembershipCreate, MembershipRead, MembershipUpdate
from src.schemas.common_schemas import MembershipShort



memberships_router = APIRouter(
    prefix="/memberships",
    tags=["memberships"]
)


@memberships_router.post("/{team_id}",
                   response_model=MembershipShort,
                   status_code=status.HTTP_201_CREATED)
async def add_member(team_id: int,
                     membership_create: MembershipCreate,
                     _: User = Depends(admin_required),
                     db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для добавления участника в команду.

    """

    stmt = (select(User)
            .where(User.id==membership_create.user_id,
                               User.is_active))

    user = await db.scalar(stmt)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Пользователь не найден")

    stmt = (select(MembershipORM)
            .where(MembershipORM.user_id==user.id,
                   MembershipORM.team_id==team_id))

    existing = await db.scalar(stmt)

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пользователь уже состоит в команде.")

    new_membership = MembershipORM(**membership_create.model_dump(), team_id=team_id,)
    db.add(new_membership)
    await db.commit()
    await db.refresh(new_membership)

    return new_membership


@memberships_router.delete("/team/{team_id}/{user_id}",
                   status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(team_id: int,
                     user_id: int,
                     _: User = Depends(admin_required),
                     db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для удаления участника из команды.

    """

    stmt = select(TeamORM).where(TeamORM.id==team_id)
    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команды не существует."
        )

    stmt = (select(MembershipORM)
            .where(
                    MembershipORM.team_id==team_id,
                    MembershipORM.user_id==user_id
                   )
    )
    membership = await db.scalar(stmt)

    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Участник не состоит в этой команде")

    if membership.role == Role.TEAM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить владельца команды"
        )

    await db.delete(membership)
    await db.commit()


@memberships_router.get("/team/{team_id}/",
                   response_model=list[MembershipRead],
                   status_code=status.HTTP_200_OK)

async def get_team_members(team_id: int,
                           _: User = Depends(admin_or_manager_required),
                           db: AsyncSession = Depends(get_async_session)):
    """

    Ручка возвращает всех участников команды.

    """

    stmt = (select(MembershipORM)
            .where(MembershipORM.team_id==team_id)
            .options(joinedload(MembershipORM.user)))

    result = await db.scalars(stmt)
    members = result.all()

    return members


@memberships_router.patch('/team/{team_id}/{user_id}',
                  response_model=MembershipRead,
                  status_code=status.HTTP_200_OK)

async def change_role(
        team_id: int,
        user_id: int,
        membership_update: MembershipUpdate,
        _: User = Depends(admin_required),
        db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для изменения роли участника в команде.

    """
    stmt = (select(MembershipORM).where(
        MembershipORM.team_id==team_id,
        MembershipORM.user_id==user_id)
            .options(joinedload(MembershipORM.user)))

    membership = await db.scalar(stmt)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="В команде нет такого участника"
    )

    membership.role = membership_update.role

    await db.commit()
    await db.refresh(membership)

    return membership