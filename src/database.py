from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


DB_URL = settings.DB_URL

async_engine = create_async_engine(DB_URL)
async_session_maker = async_sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)

