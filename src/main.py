from fastapi import FastAPI

from src.admin.models import UserAdmin, TaskAdmin
from src.auth.router import auth_router, register_router, fastapi_users_router, users_router
from src.routers.tasks import tasks_router
from src.routers.teams import teams_router


from sqladmin import Admin
from src.database import async_engine

app = FastAPI(title="TaskFlow",
              description="Система управления бизнесом для трекинга команд и их задач",
              version="1.0.1"
              )

app.include_router(auth_router, prefix="/auth/jwt", tags=["auth"])
app.include_router(register_router, prefix="/auth", tags=["auth"])
app.include_router(fastapi_users_router, prefix="/auth/users", tags=["users"])

app.include_router(tasks_router)
app.include_router(users_router)
app.include_router(teams_router)


admin = Admin(app=app,
              engine=async_engine,
              title="TaskFlowAdmin"
              )


admin.add_view(UserAdmin)
admin.add_view(TaskAdmin)


@app.get("/")
async def get_root():
    return {"message": "Добро пожаловать!"}


if __name__ == "__main__":
    pass
    # uvicorn.run(app="src.main:app", reload=True)