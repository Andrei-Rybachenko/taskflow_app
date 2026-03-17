import pytest

from tests.conftest import create_user, create_team, create_task, create_membership
from src.enums import Role


pytestmark = pytest.mark.asyncio


class TestAddComment:
    async def test_adds_comment_to_task(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1)
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.post(
            f"/comments/task/{task.id}",
            params={"team_id": 1},
            json={"content": "Отличная задача!"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Отличная задача!"
        assert data["task_id"] == task.id
        assert data["author_id"] == 1

    async def test_returns_404_for_nonexistent_task(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1)

        response = await client.post(
            "/comments/task/9999",
            params={"team_id": 1},
            json={"content": "Куда я?"}
        )
        assert response.status_code == 404

    async def test_returns_404_if_task_belongs_to_another_team(self, client, db):
        user = await create_user(db, uid=1)
        team1 = await create_team(db, owner_id=1, tid=1, name="Team 1")
        team2 = await create_team(db, owner_id=1, tid=2, name="Team 2")
        await create_membership(db, user_id=1, team_id=1)
        task = await create_task(db, team_id=2, creator_id=1)

        response = await client.post(
            f"/comments/task/{task.id}",
            params={"team_id": 1},
            json={"content": "Нет доступа"}
        )
        assert response.status_code == 404


class TestGetComments:
    async def test_returns_comments_for_task(self, client, db):
        from src.models.comments import CommentORM

        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1)
        task = await create_task(db, team_id=1, creator_id=1)

        comment = CommentORM(task_id=task.id, author_id=1, content="Тестовый комментарий")
        db.add(comment)
        await db.commit()

        response = await client.get(
            f"/comments/task/{task.id}",
            params={"team_id": 1}
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["content"] == "Тестовый комментарий"

    async def test_returns_empty_for_task_without_comments(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1)
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.get(
            f"/comments/task/{task.id}",
            params={"team_id": 1}
        )
        assert response.status_code == 200
        assert response.json() == []


class TestDeleteComment:
    async def test_deletes_own_comment(self, client, db):
        from src.models.comments import CommentORM

        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1)
        task = await create_task(db, team_id=1, creator_id=1)

        comment = CommentORM(task_id=task.id, author_id=1, content="Удали меня")
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        response = await client.delete(
            f"/comments/task/{task.id}/{comment.id}",
            params={"team_id": 1}
        )
        assert response.status_code == 204

    async def test_cannot_delete_other_users_comment(self, client, db):
        from src.models.comments import CommentORM

        user = await create_user(db, uid=1)
        other = await create_user(db, uid=2, username="other", email="other@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1)
        task = await create_task(db, team_id=1, creator_id=1)

        comment = CommentORM(task_id=task.id, author_id=2, content="Чужой комментарий")
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        response = await client.delete(
            f"/comments/task/{task.id}/{comment.id}",
            params={"team_id": 1}
        )
        assert response.status_code == 403

    async def test_returns_404_for_nonexistent_comment(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1)
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.delete(
            f"/comments/task/{task.id}/9999",
            params={"team_id": 1}
        )
        assert response.status_code == 404
