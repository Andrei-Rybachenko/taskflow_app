from fastapi import HTTPException
from starlette import status

from src.repositories.teams_repo import TeamReader, TeamWriter
from src.schemas import TeamCreate


class TeamsService:
    def __init__(self,
                 team_reader: TeamReader,
                 team_writer: TeamWriter
):
        self.team_reader = team_reader
        self.team_writer = team_writer

    async def create(self, team: TeamCreate, owner_id: int):
        new_team = team.model_dump()

        try:
            team = await self.team_writer.add_team(new_team, owner_id)
            return team
        except Exception:
            raise

    async def get_teams(self, limit: int | None = None, offset: int | None = None):
        teams = await self.team_reader.find_all(limit=limit, offset=offset)
        return teams

    async def get_team(self, team_id: int):
        team = await self.team_reader.get_team_with_relations(team_id)

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой команды не существует"
            )

        return team

    async def get_user_teams(self, user_id: int, limit: int | None = None, offset: int | None = None):
        teams = await self.team_reader.get_by_user_id(user_id, limit=limit, offset=offset)
        return teams

    async def delete_team(self, team_id: int):
        team = await self.team_reader.get_team_with_relations(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой команды не существует",
            )
        try:
            await self.team_writer.delete_team_cascade(team_id)
        except Exception:
            raise










