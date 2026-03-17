import pytest
from datetime import datetime, timezone, timedelta

from tests.conftest import create_user, create_team, create_meeting


pytestmark = pytest.mark.asyncio


class TestCreateMeeting:
    async def test_creates_meeting_successfully(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat()

        response = await client.post(
            "/meetings",
            params={"team_id": 1},
            json={"title": "Планёрка", "start_time": start, "end_time": end}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Планёрка"
        assert data["team_id"] == 1

    async def test_created_meeting_has_creator_id(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        end = (datetime.now(timezone.utc) + timedelta(days=1, hours=2)).isoformat()

        response = await client.post(
            "/meetings",
            params={"team_id": 1},
            json={"title": "Ретро", "start_time": start, "end_time": end}
        )
        assert response.status_code == 201
        assert response.json()["creator_id"] == 1


class TestGetMeetings:
    async def test_returns_empty_list_for_team_without_meetings(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.get("/meetings", params={"team_id": 1})
        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_meetings_for_team(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_meeting(db, team_id=1, creator_id=1, title="Стендап")
        await create_meeting(db, team_id=1, creator_id=1, title="Ретро")

        response = await client.get("/meetings", params={"team_id": 1})
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_does_not_return_meetings_of_other_team(self, client, db):
        user = await create_user(db, uid=1)
        team1 = await create_team(db, owner_id=1, tid=1, name="Team 1")
        team2 = await create_team(db, owner_id=1, tid=2, name="Team 2")
        await create_meeting(db, team_id=2, creator_id=1, title="Чужая встреча")

        response = await client.get("/meetings", params={"team_id": 1})
        assert response.status_code == 200
        assert response.json() == []


class TestDeleteMeeting:
    async def test_deletes_meeting_successfully(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        meeting = await create_meeting(db, team_id=1, creator_id=1)

        response = await client.delete(f"/meetings/{meeting.id}", params={"team_id": 1})
        assert response.status_code == 204

    async def test_returns_404_for_missing_meeting(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.delete("/meetings/9999", params={"team_id": 1})
        assert response.status_code == 404

    async def test_cannot_delete_meeting_from_other_team(self, client, db):
        user = await create_user(db, uid=1)
        team1 = await create_team(db, owner_id=1, tid=1, name="Team 1")
        team2 = await create_team(db, owner_id=1, tid=2, name="Team 2")
        meeting = await create_meeting(db, team_id=2, creator_id=1)

        response = await client.delete(f"/meetings/{meeting.id}", params={"team_id": 1})
        assert response.status_code == 404
