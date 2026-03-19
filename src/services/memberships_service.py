from fastapi import HTTPException
from starlette import status

from src.enums import Role
from src.repositories.membership_repo import MembershipsRepository
from src.repositories.tasks_repo import TasksRepository
from src.repositories.teams_repo import TeamsRepository
from src.repositories.users_repo import UsersRepository
from src.schemas import MembershipCreate, MembershipUpdate


class MembershipsService:
    def __init__(
            self,
            memberships_repo: MembershipsRepository,
            tasks_repo: TasksRepository,
            teams_repo: TeamsRepository,
            users_repo: UsersRepository
    ):
        self.memberships_repo = memberships_repo
        self.tasks_repo = tasks_repo
        self.teams_repo = teams_repo
        self.users_repo = users_repo


    async def add_member(
            self,
            new_membership: MembershipCreate
    ):
        user = await self.users_repo.get_user(new_membership.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        existing = await self.memberships_repo.get_membership(new_membership.user_id,
                                                              new_membership.team_id)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь уже состоит в команде.",
            )

        new_membership = new_membership.model_dump()
        membership = await self.memberships_repo.add_one(new_membership)

        return membership


    async def get(self, user_id: int, team_id: int):
        membership = await self.memberships_repo.get_membership(user_id, team_id)
        return membership


    async def delete(self, user_id: int, team_id: int):
        team = await self.teams_repo.find_one(team_id)

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Команды не существует."
            )

        membership = await self.memberships_repo.get_membership(user_id, team_id)

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

    async def get_members(self, team_id: int):
        members = await self.memberships_repo.get_team_members(team_id)
        return members


    async def change_role(
            self,
            membership_to_update: MembershipUpdate,
            user_id: int,
            team_id: int
    ):
        membership = await self.memberships_repo.get_membership(user_id, team_id)

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="В команде нет такого участника",
            )

        membership_dict = membership_to_update.model_dump(exclude_unset=True)
        updated_membership = await self.memberships_repo.update(membership_dict, user_id, team_id)

        return updated_membership

