from fastapi import HTTPException
from starlette import status

from src.enums import Role
from src.repositories.membership_repo import MembershipReader, MembershipWriter

from src.repositories.teams_repo import TeamReader
from src.repositories.users_repo import UserReader
from src.schemas import MembershipCreate, MembershipUpdate


class MembershipsService:
    def __init__(
            self,
            membership_reader: MembershipReader,
            membership_writer: MembershipWriter,
            team_reader: TeamReader,
            user_reader: UserReader
    ):
        self.membership_reader = membership_reader
        self.membership_writer = membership_writer
        self.team_reader = team_reader
        self.user_reader = user_reader


    async def add_member(
            self,
            new_membership: MembershipCreate
    ):
        user = await self.user_reader.get_user(new_membership.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        existing = await self.membership_reader.get_membership(new_membership.user_id,
                                                              new_membership.team_id)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь уже состоит в команде.",
            )

        data = new_membership.model_dump()
        try:
            await self.membership_writer.add_one(data)
        except Exception:
            raise

        return await self.membership_reader.get_membership(data["user_id"], data["team_id"])


    async def get(self, user_id: int, team_id: int):
        membership = await self.membership_reader.get_membership(user_id, team_id)
        return membership


    async def delete(self, user_id: int, team_id: int):
        team = await self.team_reader.get_team_with_relations(team_id)

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Команды не существует."
            )

        membership = await self.membership_reader.get_membership(user_id, team_id)

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Участник не состоит в этой команде",
            )

        if membership.role == Role.TEAM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить владельца команды",
            )

        try:
            await self.membership_writer.delete_member(user_id, team_id)
        except Exception:
            raise

    async def get_members(self, team_id: int):
        members = await self.membership_reader.get_team_members(team_id)
        return members

    async def get_user_memberships(self, user_id: int):
        memberships = await self.membership_reader.get_user_memberships(user_id)
        return memberships

    async def change_role(
            self,
            membership_to_update: MembershipUpdate,
            user_id: int,
            team_id: int
    ):
        membership = await self.membership_reader.get_membership(user_id, team_id)

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="В команде нет такого участника",
            )

        membership_dict = membership_to_update.model_dump(exclude_unset=True)
        try:
            updated_membership = await self.membership_writer.update(membership_dict, user_id, team_id)
        except Exception:
            raise

        return await self.membership_reader.get_membership(updated_membership.user_id,
                                                          updated_membership.team_id)

