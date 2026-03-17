
import pytest

from tests.conftest import create_user, create_team, create_membership
from src.enums import Role


pytestmark = pytest.mark.asyncio


class TestAddMember:
    async def test_adds_member_successfully(self, client, db):
        owner = await create_user(db, uid=1)
        member = await create_user(db, uid=2, username="member", email="member@test.com")
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.post(
            "/memberships/1",
            json={"user_id": 2, "role": Role.EMPLOYEE}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == 2
        assert data["team_id"] == 1

    async def test_cannot_add_nonexistent_user(self, client, db):
        owner = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.post(
            "/memberships/1",
            json={"user_id": 9999, "role": Role.EMPLOYEE}
        )
        assert response.status_code == 404

    async def test_cannot_add_duplicate_member(self, client, db):
        owner = await create_user(db, uid=1)
        member = await create_user(db, uid=2, username="member", email="member@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=2, team_id=1)

        response = await client.post(
            "/memberships/1",
            json={"user_id": 2, "role": Role.EMPLOYEE}
        )
        assert response.status_code == 400


class TestDeleteMember:
    async def test_removes_member_successfully(self, client, db):
        owner = await create_user(db, uid=1)
        member = await create_user(db, uid=2, username="member", email="member@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=2, team_id=1, role=Role.EMPLOYEE)

        response = await client.delete("/memberships/team/1/2")
        assert response.status_code == 204

    async def test_returns_404_if_team_not_found(self, client, db):
        response = await client.delete("/memberships/team/9999/1")
        assert response.status_code == 404

    async def test_returns_404_if_member_not_in_team(self, client, db):
        owner = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.delete("/memberships/team/1/9999")
        assert response.status_code == 404

    async def test_cannot_remove_team_admin(self, client, db):
        owner = await create_user(db, uid=1)
        admin = await create_user(db, uid=2, username="admin2", email="admin2@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=2, team_id=1, role=Role.TEAM_ADMIN)

        response = await client.delete("/memberships/team/1/2")
        assert response.status_code == 400


class TestGetTeamMembers:
    async def test_returns_all_team_members(self, client, db):
        owner = await create_user(db, uid=1)
        member = await create_user(db, uid=2, username="member", email="m@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1, role=Role.MANAGER)
        await create_membership(db, user_id=2, team_id=1, role=Role.EMPLOYEE)

        response = await client.get("/memberships/team/1/", params={"team_id": 1})
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_returns_empty_for_team_without_members(self, client, db):
        owner = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.get("/memberships/team/1/", params={"team_id": 1})
        assert response.status_code == 200
        assert response.json() == []


class TestChangeRole:
    async def test_changes_role_successfully(self, client, db):
        owner = await create_user(db, uid=1)
        member = await create_user(db, uid=2, username="member", email="m@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=2, team_id=1, role=Role.EMPLOYEE)

        response = await client.patch(
            "/memberships/team/1/2",
            json={"role": Role.MANAGER}
        )
        assert response.status_code == 200
        assert response.json()["role"] == Role.MANAGER

    async def test_returns_404_if_not_member(self, client, db):
        owner = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.patch(
            "/memberships/team/1/9999",
            json={"role": Role.MANAGER}
        )
        assert response.status_code == 404
