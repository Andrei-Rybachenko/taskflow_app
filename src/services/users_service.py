from fastapi import HTTPException
from starlette import status

from src.repositories.membership_repo import MembershipsRepository, MembershipReader
from src.repositories.users_repo import UsersRepository, UserReader, UserWriter


class UsersService:
    def __init__(
            self,
            user_reader: UserReader,
            user_writer: UserWriter,
            membership_reader: MembershipReader
    ):
        self.user_reader = user_reader
        self.user_writer = user_writer
        self.membership_reader = membership_reader


    async def get_users(self):
        users = await self.user_reader.find_all()

        return users

    async def get_user_teams_members(self, user_id: int, team_id: int):
        membership = await self.membership_reader.get_membership(user_id, team_id)

        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Вы не являетесь участником этой команды.")

        members = await self.membership_reader.get_team_members(team_id)

        return members


    async def deactivate_me(self, user_id: int):
        user = await self.user_writer.deactivate_user(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        return user