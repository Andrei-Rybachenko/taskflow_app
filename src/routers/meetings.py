from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.models import User
from src.dependencies import admin_or_manager_required, meetings_service
from src.schemas import MeetingRead, MeetingCreate
from src.services.meetings_service import MeetingsService


meetings_router = APIRouter(prefix="/meetings", tags=["meetings"])


@meetings_router.post(
    "", response_model=MeetingRead, status_code=status.HTTP_201_CREATED
)
async def create_meeting(
    meeting_data: MeetingCreate,
    service: Annotated[MeetingsService, Depends(meetings_service)],
    current_user: User = Depends(admin_or_manager_required)
):
    new_meeting = await service.create(meeting_data, current_user.id)

    return new_meeting


@meetings_router.get(
    "{team_id}",
    response_model=list[MeetingRead],
    status_code=status.HTTP_200_OK
)
async def get_meetings(
    team_id: int,
    service: Annotated[MeetingsService, Depends(meetings_service)],
    _: User = Depends(admin_or_manager_required)
):
    meetings = await service.get_team_meetings(team_id)

    return meetings


@meetings_router.get(
    "{meeting_id}",
    response_model=MeetingRead,
    status_code=status.HTTP_200_OK
)
async def get_meeting(
    meeting_id: int,
    service: Annotated[MeetingsService, Depends(meetings_service)],
    _: User = Depends(admin_or_manager_required)
):
    meeting = await service.get_meeting(meeting_id)

    return meeting




@meetings_router.delete("/{meeting_id}",
                        status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting_by_id(
    meeting_id: int,
    service: Annotated[MeetingsService, Depends(meetings_service)],
    _: User = Depends(admin_or_manager_required)
):
    await service.delete_meeting(meeting_id)