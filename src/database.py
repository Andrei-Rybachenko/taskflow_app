from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker,
                                    AsyncSession)
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

DB_URL = settings.DB_URL

async_engine = create_async_engine(DB_URL, echo=True)
async_session_maker = async_sessionmaker(
    bind=async_engine, expire_on_commit=False, class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
