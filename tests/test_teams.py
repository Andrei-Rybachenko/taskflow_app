"""
Тесты для роутера /teams
"""
import pytest

from tests.conftest import create_user, create_team, create_membership
from src.enums import Role


pytestmark = pytest.mark.asyncio


class TestCreateTeam:
    async def test_creates_team_successfully(self, client, db):
        user = await create_user(db, uid=1)

        response = await client.post("/teams/create", json={"name": "Dream Team"})
        assert response.status_code == 201
        assert response.json()["name"] == "Dream Team"

    async def test_created_team_has_id(self, client, db):
        user = await create_user(db, uid=1)

        response = await client.post("/teams/create", json={"name": "My Team"})
        assert "id" in response.json()


class TestGetAllTeams:
    async def test_returns_empty_list_when_no_teams(self, client, db):
        response = await client.get("/teams/all_teams")
        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_all_teams(self, client, db):
        user = await create_user(db, uid=1)
        await create_team(db, owner_id=1, tid=1, name="Team Alpha")
        await create_team(db, owner_id=1, tid=2, name="Team Beta")

        response = await client.get("/teams/all_teams")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_teams_ordered_by_id(self, client, db):
        user = await create_user(db, uid=1)
        await create_team(db, owner_id=1, tid=1, name="First")
        await create_team(db, owner_id=1, tid=2, name="Second")

        response = await client.get("/teams/all_teams")
        names = [t["name"] for t in response.json()]
        assert names == ["First", "Second"]


class TestGetTeamById:
    async def test_returns_team_by_id(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1, name="The A-Team")

        response = await client.get("/teams/1", params={"team_id": 1})
        assert response.status_code == 200
        assert response.json()["name"] == "The A-Team"

    async def test_returns_404_for_missing_team(self, client, db):
        response = await client.get("/teams/9999", params={"team_id": 9999})
        assert response.status_code == 404

    async def test_team_includes_members_tasks_meetings(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.get("/teams/1", params={"team_id": 1})
        data = response.json()
        assert "memberships" in data
        assert "tasks" in data
        assert "meetings" in data


class TestGetUserTeams:
    async def test_returns_teams_for_user(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1, name="Team X")
        await create_membership(db, user_id=1, team_id=1, role=Role.TEAM_ADMIN)

        response = await client.get("/teams/user/1")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Team X"

    async def test_returns_empty_for_user_without_teams(self, client, db):
        user = await create_user(db, uid=1)

        response = await client.get("/teams/user/1")
        assert response.status_code == 200
        assert response.json() == []
