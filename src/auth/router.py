
from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.users import auth_backend, get_user_manager
from src.models.users import User
from src.auth.schemas import UserRead, UserCreate, UserUpdate
from src.database import get_async_session

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

auth_router = fastapi_users.get_auth_router(auth_backend)
register_router = fastapi_users.get_register_router(UserRead, UserCreate)
fastapi_users_router = fastapi_users.get_users_router(UserRead, UserUpdate)


users_router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@users_router.get("/", response_model=list[UserRead], status_code=status.HTTP_200_OK)
async def get_users(db: AsyncSession = Depends(get_async_session)):
    """

    Ручка возвращает всех пользователей из базы.

    """
    stmt = select(User).order_by(User.id)

    result = await db.scalars(stmt)
    return result.all()
