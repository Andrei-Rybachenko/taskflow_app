"""
Тесты для роутера /tasks
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta

from tests.conftest import create_user, create_team, create_task, create_membership
from src.enums import TaskStatus, Role


pytestmark = pytest.mark.asyncio


class TestGetAllTasks:
    async def test_returns_empty_list_when_no_tasks(self, client):
        response = await client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_all_tasks(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_task(db, team_id=1, creator_id=1, title="Task 1")
        await create_task(db, team_id=1, creator_id=1, title="Task 2")

        response = await client.get("/tasks")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_tasks_have_correct_fields(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1, title="Важная задача")

        response = await client.get("/tasks")
        data = response.json()
        assert data[0]["title"] == "Важная задача"
        assert data[0]["status"] == TaskStatus.OPEN


class TestGetMyTasks:
    async def test_returns_tasks_for_current_user(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_task(db, team_id=1, creator_id=1, title="Моя задача", executor_id=1)

        response = await client.get("/tasks/my")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Моя задача"

    async def test_returns_empty_if_no_tasks_assigned(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_task(db, team_id=1, creator_id=1, title="Чужая задача", executor_id=2)

        response = await client.get("/tasks/my")
        assert response.status_code == 200
        assert response.json() == []


class TestCreateTask:
    async def test_creates_task_successfully(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        deadline = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

        response = await client.post(
            "/tasks/1/create",
            json={"title": "Новая задача", "description": "Описание", "deadline": deadline}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Новая задача"
        assert data["team_id"] == 1
        assert data["status"] == TaskStatus.OPEN

    async def test_created_task_has_creator_id(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        deadline = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

        response = await client.post(
            "/tasks/1/create",
            json={"title": "Задача", "description": "Описание", "deadline": deadline}
        )
        assert response.status_code == 201
        assert response.json()["creator_id"] == 1


class TestGetTaskById:
    async def test_returns_task_by_id(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1, title="Найди меня")

        response = await client.get(f"/tasks/{task.id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Найди меня"

    async def test_returns_404_for_missing_task(self, client, db):
        response = await client.get("/tasks/9999")
        assert response.status_code == 404

    async def test_task_includes_comments_and_executor(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1, executor_id=1)

        response = await client.get(f"/tasks/{task.id}")
        data = response.json()
        assert "comments" in data
        assert "executor" in data


class TestUpdateTask:
    async def test_updates_task_title(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1, title="Старый заголовок")

        response = await client.patch(
            f"/tasks/{task.id}/update",
            params={"team_id": 1},
            json={"title": "Новый заголовок"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Новый заголовок"

    async def test_updates_task_status(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.patch(
            f"/tasks/{task.id}/update",
            params={"team_id": 1},
            json={"status": TaskStatus.IN_PROGRESS}
        )
        assert response.status_code == 200
        assert response.json()["status"] == TaskStatus.IN_PROGRESS

    async def test_returns_404_for_missing_task(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.patch(
            "/tasks/9999/update",
            params={"team_id": 1},
            json={"title": "Не найдётся"}
        )
        assert response.status_code == 404


class TestDeleteTask:
    async def test_deletes_task_successfully(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.delete(f"/tasks/{task.id}/delete")
        assert response.status_code == 204

        response = await client.get(f"/tasks/{task.id}")
        assert response.status_code == 404

    async def test_returns_404_for_missing_task(self, client, db):
        response = await client.delete("/tasks/9999/delete")
        assert response.status_code == 404


class TestAssignTask:
    async def test_assigns_task_to_user(self, client, db):
        user = await create_user(db, uid=1)
        executor = await create_user(db, uid=2, username="executor", email="exec@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=2, team_id=1, role=Role.EMPLOYEE)
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.patch(
            f"/tasks/{task.id}/assign",
            params={"user_to_assign": 2}
        )
        assert response.status_code == 200
        assert response.json()["executor_id"] == 2

    async def test_cannot_reassign_already_assigned_task(self, client, db):
        user = await create_user(db, uid=1)
        executor = await create_user(db, uid=2, username="executor", email="exec@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1, executor_id=1)

        response = await client.patch(
            f"/tasks/{task.id}/assign",
            params={"user_to_assign": 2}
        )
        assert response.status_code == 400

    async def test_cannot_assign_user_from_different_team(self, client, db):
        user = await create_user(db, uid=1)
        outsider = await create_user(db, uid=2, username="outsider", email="out@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.patch(
            f"/tasks/{task.id}/assign",
            params={"user_to_assign": 2}
        )
        assert response.status_code == 400


class TestGetTasksByTeam:
    async def test_returns_tasks_for_team(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_task(db, team_id=1, creator_id=1, title="Задача команды")

        response = await client.get("/tasks/1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Задача команды"

    async def test_returns_404_for_nonexistent_team(self, client, db):
        response = await client.get("/tasks/9999/tasks")
        assert response.status_code == 404

    async def test_returns_404_when_team_has_no_tasks(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.get("/tasks/1/tasks")
        assert response.status_code == 404
