import asyncio
import contextlib

from fastapi_users.exceptions import UserAlreadyExists

from src.auth.users import get_user_manager, get_user_db
from src.auth.schemas import UserCreate
from src.dependencies import get_async_session

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_superuser():
    email = input("Email: ")
    password = input("Password: ")
    username = input("Username: ")

    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=email,
                            password=password,
                            username=username,
                            is_superuser=True
                        )
                    )
                    print(f"User created {user}")
                    return user
    except UserAlreadyExists:
        print(f"User {email} already exists")
        raise
    

if __name__ == "__main__":
    asyncio.run(create_superuser())