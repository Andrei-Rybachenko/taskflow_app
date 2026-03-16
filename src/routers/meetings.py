from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.models import User, MeetingORM
from src.database import get_async_session
from src.dependencies import admin_or_manager_required
from src.schemas import MeetingRead, MeetingCreate


meetings_router = APIRouter(
    prefix="/meetings",
    tags=["meetings"]
)


@meetings_router.post('',
                  response_model=MeetingRead,
                  status_code=status.HTTP_201_CREATED)
async def create_meeting(
        team_id: int,
        meeting_data: MeetingCreate,
        current_user: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    new_meeting = MeetingORM(**meeting_data.model_dump(),
                             team_id=team_id,
                             creator_id=current_user.id)

    db.add(new_meeting)
    await db.commit()
    await db.refresh(new_meeting)

    return new_meeting


@meetings_router.get('',
                  response_model=list[MeetingRead],
                  status_code=status.HTTP_200_OK)
async def get_meetings(
        team_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = select(MeetingORM).where(MeetingORM.team_id==team_id)
    result = await db.scalars(stmt)
    meetings = result.all()

    return meetings


@meetings_router.delete('/{meeting_id}',
                  status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting_by_id(
        team_id: int,
        meeting_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(MeetingORM)
            .where(MeetingORM.team_id == team_id,
                   MeetingORM.id==meeting_id))

    meeting = await db.scalar(stmt)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Встреча не найдена."
        )

    await db.delete(meeting)
    await db.commit()