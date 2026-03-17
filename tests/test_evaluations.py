
import pytest

from tests.conftest import create_user, create_team, create_task, create_membership
from src.enums import TaskStatus, Role
from src.models.evaluations import EvaluationORM


pytestmark = pytest.mark.asyncio


class TestAddEvaluation:
    async def test_adds_score_for_task(self, client, db):
        manager = await create_user(db, uid=1, username="manager", email="mgr@test.com")
        executor = await create_user(db, uid=2, username="executor", email="exec@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1, role=Role.MANAGER)
        task = await create_task(db, team_id=1, creator_id=1,
                                 status=TaskStatus.FINISHED, executor_id=2)

        response = await client.post(
            f"/evaluations/task/{task.id}",
            params={"team_id": 1},
            json={"score": 5, "comment": "Отличная работа", "reviewer_id": 1}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["score"] == 5
        assert data["employee_id"] == 2

    async def test_returns_404_for_nonexistent_task(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1, role=Role.MANAGER)

        response = await client.post(
            "/evaluations/task/9999",
            params={"team_id": 1},
            json={"score": 3, "comment": "ok", "reviewer_id": 1}
        )
        assert response.status_code == 404

    async def test_returns_400_if_task_not_assigned(self, client, db):
        manager = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1, role=Role.MANAGER)
        # executor_id=None — задача не назначена
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.post(
            f"/evaluations/task/{task.id}",
            params={"team_id": 1},
            json={"score": 4, "comment": "Хорошо", "reviewer_id": 1}
        )
        assert response.status_code == 400

    async def test_cannot_add_duplicate_evaluation(self, client, db):
        manager = await create_user(db, uid=1)
        executor = await create_user(db, uid=2, username="exec", email="exec@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        await create_membership(db, user_id=1, team_id=1, role=Role.MANAGER)
        task = await create_task(db, team_id=1, creator_id=1,
                                 status=TaskStatus.FINISHED, executor_id=2)

        eval_orm = EvaluationORM(task_id=task.id, reviewer_id=1,
                                 employee_id=2, score=4, comment="First")
        db.add(eval_orm)
        await db.commit()

        response = await client.post(
            f"/evaluations/task/{task.id}",
            params={"team_id": 1},
            json={"score": 5, "comment": "Second", "reviewer_id": 1}
        )
        assert response.status_code == 400


class TestGetEvaluation:
    async def test_returns_evaluation_for_task(self, client, db):
        manager = await create_user(db, uid=1)
        executor = await create_user(db, uid=2, username="exec", email="exec@test.com")
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1, executor_id=2)

        eval_orm = EvaluationORM(task_id=task.id, reviewer_id=1,
                                 employee_id=2, score=5, comment="Отлично")
        db.add(eval_orm)
        await db.commit()

        response = await client.get(
            f"/evaluations/task/{task.id}",
            params={"team_id": 1}
        )
        assert response.status_code == 200
        assert response.json()["score"] == 5

    async def test_returns_400_if_no_evaluation(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)
        task = await create_task(db, team_id=1, creator_id=1)

        response = await client.get(
            f"/evaluations/task/{task.id}",
            params={"team_id": 1}
        )
        assert response.status_code == 400

    async def test_returns_404_for_nonexistent_task(self, client, db):
        user = await create_user(db, uid=1)
        team = await create_team(db, owner_id=1, tid=1)

        response = await client.get(
            "/evaluations/task/9999",
            params={"team_id": 1}
        )
        assert response.status_code == 404
