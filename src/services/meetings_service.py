from fastapi import HTTPException
from starlette import status

from src.repositories.meetings_repo import MeetingReader, MeetingWriter
from src.schemas import MeetingCreate


class MeetingsService:
    def __init__(
            self,
            meeting_reader: MeetingReader,
            meeting_writer: MeetingWriter
    ):
        self.meeting_reader = meeting_reader
        self.meeting_writer = meeting_writer


    async def create(self, meeting: MeetingCreate, creator_id: int):
        overlapping_meeting = await self.meeting_reader.overlapping_meeting(meeting)

        if overlapping_meeting:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Встреча накладывается на другую встречу: "
                       f"{overlapping_meeting.title} "
                       f"({overlapping_meeting.start_time} - {overlapping_meeting.end_time})",
            )

        new_meeting = meeting.model_dump()
        try:
            meeting = await self.meeting_writer.add_meeting(new_meeting, creator_id)
        except Exception:
            raise

        return await self.meeting_reader.get_meeting_with_relations(meeting.id)


    async def delete_meeting(self, meeting_id: int, team_id: int | None = None):
        meeting = await self.meeting_reader.get_meeting_with_relations(meeting_id)

        if not meeting or team_id is not None and meeting.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Встреча не найдена."
            )

        try:
            await self.meeting_writer.delete(meeting_id)
        except Exception:
            raise


    async def get_team_meetings(self, team_id: int, limit: int | None = None, offset: int | None = None):
        meetings = await self.meeting_reader.get_meetings_by_team_id(team_id, limit=limit, offset=offset)

        return meetings or []


    async def get_meeting(self, meeting_id: int):
        meeting = await self.meeting_reader.get_meeting_with_relations(meeting_id)

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Встреча не найдена."
            )

        return meeting
