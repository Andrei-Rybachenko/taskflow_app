from fastapi import HTTPException
from starlette import status

from src.repositories.teams_repo import TeamsRepository
from src.schemas import TeamCreate


class TeamsService:
    def __init__(self, teams_repo: TeamsRepository):
        self.teams_repo = teams_repo

    async def create(self, team: TeamCreate, owner_id: int):
        new_team = team.model_dump()

        try:
            team = await self.teams_repo.add_team(new_team, owner_id)
            return team
        except Exception:
            await self.teams_repo.session.rollback()
            raise

    async def get_teams(self, limit: int | None = None, offset: int | None = None):
        teams = await self.teams_repo.find_all(limit=limit, offset=offset)
        return teams

    async def get_team(self, team_id: int):
        team = await self.teams_repo.get_team_with_relations(team_id)

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой команды не существует"
            )

        return team

    async def get_user_teams(self, user_id: int, limit: int | None = None, offset: int | None = None):
        teams = await self.teams_repo.get_by_user_id(user_id, limit=limit, offset=offset)
        return teams

    async def delete_team(self, team_id: int):
        team = await self.teams_repo.find_one(team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой команды не существует",
            )
        try:
            await self.teams_repo.delete_team_cascade(team_id)
        except Exception:
            await self.teams_repo.session.rollback()
            raise










