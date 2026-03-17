import uvicorn
from fastapi import FastAPI

from src.admin.models import (UserAdmin, TaskAdmin,
                              TeamAdmin, MembershipsAdmin,
                              MeetingsAdmin, CommentsAdmin,
                              EvaluationsAdmin)
from src.auth.router import (auth_router, register_router,
                             fastapi_users_router, users_router)
from src.routers.calendar import calendar_router
from src.routers.comments import comments_router
from src.routers.evaluations import evaluations_router
from src.routers.meetings import meetings_router
from src.routers.memberships import memberships_router

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
app.include_router(comments_router)
app.include_router(evaluations_router)
app.include_router(meetings_router)
app.include_router(memberships_router)
app.include_router(calendar_router)



admin = Admin(app=app,
              engine=async_engine,
              title="TaskFlowAdmin"
              )

admin.add_view(UserAdmin)
admin.add_view(TaskAdmin)
admin.add_view(TeamAdmin)
admin.add_view(MembershipsAdmin)
admin.add_view(MeetingsAdmin)
admin.add_view(CommentsAdmin)
admin.add_view(EvaluationsAdmin)



if __name__ == "__main__":
    uvicorn.run(app="src.main:app", reload=True)