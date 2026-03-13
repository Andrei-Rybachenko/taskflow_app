# from fastapi import Depends
# from fastapi_users import BaseUserManager, IntegerIDMixin
# from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
# from starlette.requests import Request
#
# from src.auth.models import get_user_db
#
# SECRET = "SECRET_KEY"
#
#
# class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
#     reset_password_token_secret = SECRET
#     verification_token_secret = SECRET
#
#     async def on_after_register(self, user: User, request: Request | None = None):
#         print(f"User {user.id} has registered.")
#
#
# async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
#     yield UserManager(user_db)