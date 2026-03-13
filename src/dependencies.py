from fastapi import Depends, HTTPException
from starlette import status

from src.auth.users import current_active_user
from src.models.users import User


# async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
#     """
#     Предоставляет асинхронную сессию SQLAlchemy для работы с базой данных PostgreSQL.
#     """
#     async with async_session_maker() as session:
#         yield session


async def admin_required(user: User = Depends(current_active_user)):
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have a permission to create a team."
        )
    return user

