
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database import Base, get_async_session
from src.main import app
from src.models.users import User
from src.models.teams import TeamORM
from src.models.tasks import TaskORM
from src.models.meetings import MeetingORM
from src.models.memberships import MembershipORM
from src.enums import TaskStatus, Role


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Создаёт движок SQLite и поднимает схему перед каждым тестом."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(engine):
    """Возвращает сессию, привязанную к тестовому движку."""
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(engine):
    """
    Тестовый HTTP-клиент.
    Переопределяет get_async_session на тестовый движок.
    Аутентификация замокана — current_active_user возвращает суперпользователя.
    """
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_session

    # Суперпользователь для всех запросов
    from src.routers import current_active_user
    superuser = make_superuser()
    app.dependency_overrides[current_active_user] = lambda: superuser

    # Также перекрываем зависимости безопасности
    from src.dependencies import admin_required, admin_or_manager_required, team_member_required, manager_required
    app.dependency_overrides[admin_required] = lambda: superuser
    app.dependency_overrides[admin_or_manager_required] = lambda: superuser
    app.dependency_overrides[team_member_required] = lambda: superuser
    app.dependency_overrides[manager_required] = lambda: superuser

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


def make_superuser(uid: int = 1) -> User:
    user = User()
    user.id = uid
    user.username = "superuser"
    user.email = "super@test.com"
    user.hashed_password = "hashed"
    user.is_active = True
    user.is_superuser = True
    user.is_verified = True
    return user


async def create_user(db: AsyncSession, uid: int = 1, username: str = "testuser",
                      email: str = "test@test.com", superuser: bool = False) -> User:
    user = User()
    user.id = uid
    user.username = username
    user.email = email
    user.hashed_password = "hashed"
    user.is_active = True
    user.is_superuser = superuser
    user.is_verified = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_team(db: AsyncSession, owner_id: int, tid: int = 1,
                      name: str = "Test Team") -> TeamORM:
    team = TeamORM(id=tid, name=name, owner_id=owner_id)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


async def create_task(db: AsyncSession, team_id: int, creator_id: int,
                      title: str = "Test Task",
                      deadline: datetime | None = None,
                      status: TaskStatus = TaskStatus.OPEN,
                      executor_id: int | None = None) -> TaskORM:
    if deadline is None:
        deadline = datetime.now(timezone.utc) + timedelta(days=7)
    task = TaskORM(
        title=title,
        description="Test description",
        team_id=team_id,
        creator_id=creator_id,
        deadline=deadline,
        status=status,
        executor_id=executor_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def create_meeting(db: AsyncSession, team_id: int, creator_id: int,
                         title: str = "Test Meeting",
                         start_time: datetime | None = None,
                         end_time: datetime | None = None) -> MeetingORM:
    if start_time is None:
        start_time = datetime.now(timezone.utc) + timedelta(days=1)
    if end_time is None:
        end_time = start_time + timedelta(hours=1)
    meeting = MeetingORM(
        title=title,
        team_id=team_id,
        creator_id=creator_id,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return meeting


async def create_membership(db: AsyncSession, user_id: int, team_id: int,
                            role: Role = Role.EMPLOYEE) -> MembershipORM:
    membership = MembershipORM(user_id=user_id, team_id=team_id, role=role)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership
