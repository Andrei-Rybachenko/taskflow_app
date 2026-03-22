from typing import Union

from fastapi_users import models, FastAPIUsers, InvalidPasswordException
from fastapi_users.authentication import (
    JWTStrategy,
    AuthenticationBackend,
    CookieTransport
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.schemas import UserCreate
from src.models.users import User
from fastapi import Depends
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from src.database import get_async_session

from src.config import settings


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):

    async def validate_password(
        self,
        password: str,
        user: Union[UserCreate, User],
    ) -> None:
        if len(password) < 8:
            raise InvalidPasswordException(
                reason="Пароль должен состоять минимум из 8 символов."
            )

        if password.isdigit():
            raise InvalidPasswordException(
                reason="Пароль не должен состоять только из цифр"
            )

        if user.email in password:
            raise InvalidPasswordException(
                reason="Пароль не должен содержать e-mail.")


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
        user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(
    cookie_name="auth",
    cookie_max_age=3600,
    cookie_secure=False,
)


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=settings.SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])
