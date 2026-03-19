from fastapi import HTTPException
from starlette import status

from src.repositories.teams_repo import TeamsRepository
from src.schemas import TeamCreate


class TeamsService:
    def __init__(self, teams_repo: TeamsRepository):
        self.teams_repo = teams_repo

    async def create(self, team: TeamCreate, owner_id: int):
        new_team = team.model_dump()
        team = await self.teams_repo.add_team(new_team, owner_id)
        return team

    async def get_teams(self):
        teams = await self.teams_repo.find_all()
        return teams

    async def get_team(self, team_id: int):
        team = await self.teams_repo.find_one(team_id)

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой команды не существует"
            )

        return team

    async def get_user_teams(self, user_id: int):
        teams = await self.teams_repo.get_by_user_id(user_id)
        return teams











    # async def get_users_tasks(self, current_user: int):
    #     tasks = await self.tasks_repo.get_by_user_id(current_user)
    #     return tasks
    #
    # async def update(self, task: TaskCreate, team: int, creator_id: int):
    #     task = pass