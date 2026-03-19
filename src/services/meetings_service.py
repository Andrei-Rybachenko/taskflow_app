from fastapi import HTTPException
from starlette import status

from src.repositories.meetings_repo import MeetingsRepository
from src.schemas import MeetingCreate


class MeetingsService:
    def __init__(
            self,
            meetings_repo: MeetingsRepository
    ):
        self.meetings_repo = meetings_repo

    async def create(self, meeting: MeetingCreate, creator_id: int):
        overlapping_meeting = await self.meetings_repo.overlapping_meeting(meeting)

        if overlapping_meeting:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Встреча накладывается на другую встречу: "
                       f"{overlapping_meeting.title} "
                       f"({overlapping_meeting.start_time} - {overlapping_meeting.end_time})",
            )

        new_meeting = meeting.model_dump()
        meeting = await self.meetings_repo.add_meeting(new_meeting, creator_id)

        return meeting


    async def delete_meeting(self, meeting_id: int):

        meeting = await self.meetings_repo.find_one(meeting_id)

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Встреча не найдена."
            )

        await self.meetings_repo.delete(meeting_id)


    async def get_team_meetings(self, team_id: int):
        meetings = await self.meetings_repo.get_meetings_by_team_id(team_id)

        if not meetings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Встречи не найдены"
            )

        return meetings


    async def get_meeting(self, meeting_id: int):
        meeting = await self.meetings_repo.find_one(meeting_id)

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Встреча не найдена."
            )

        return meeting
