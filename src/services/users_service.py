from fastapi import HTTPException
from starlette import status

from src.repositories.membership_repo import MembershipsRepository
from src.repositories.users_repo import UsersRepository



class UsersService:
    def __init__(
            self,
            users_repo: UsersRepository,
            memberships_repo: MembershipsRepository
    ):
        self.users_repo = users_repo
        self.memberships_repo = memberships_repo


    async def get_users(self):
        users = await self.users_repo.find_all()

        return users

    async def get_user_teams_members(self, user_id: int, team_id: int):
        membership = await self.memberships_repo.get_membership(user_id, team_id)

        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Вы не являетесь участником этой команды.")

        members = await self.memberships_repo.get_team_members(team_id)

        return members