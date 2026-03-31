import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import HTTPException

from src.admin.models import (
    UserAdmin,
    TaskAdmin,
    TeamAdmin,
    MembershipsAdmin,
    MeetingsAdmin,
    CommentsAdmin,
    EvaluationsAdmin,
)
from src.auth.router import (
    auth_router,
    register_router,
    fastapi_users_router,
    users_router,
)

from src.routers.calendar import calendar_router
from src.routers.comments import comments_router
from src.routers.evaluations import evaluations_router
from src.routers.meetings import meetings_router
from src.routers.memberships import memberships_router

from src.routers.tasks import tasks_router
from src.routers.teams import teams_router


from sqladmin import Admin
from src.database import async_engine
from src.routers.web_ui import web_router

app = FastAPI(
    title="TaskFlow",
    description="Система управления бизнесом для трекинга команд и их задач",
    version="1.0.1",
)

templates = Jinja2Templates(directory="templates")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Для API оставляем JSON (по умолчанию), а для UI показываем HTML.
    if request.url.path.startswith("/ui"):
        if exc.status_code in (401, 403):
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "user": None,
                    "message": "Недостаточно прав. Войдите или обратитесь к администратору.",
                    "back_url": "/ui/login",
                },
                status_code=exc.status_code,
            )
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "user": None,
                "message": str(exc.detail),
                "back_url": "/ui/teams",
            },
            status_code=exc.status_code,
        )

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth_router, prefix="/auth", tags=["Авторизация"])
app.include_router(register_router, prefix="/auth", tags=["Авторизация"])
app.include_router(fastapi_users_router, prefix="/auth/users", tags=["Пользователи"])

app.include_router(tasks_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(teams_router, prefix="/api")
app.include_router(comments_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(meetings_router, prefix="/api")
app.include_router(memberships_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(web_router)




admin = Admin(app=app, engine=async_engine, title="Админка TaskFlow")

admin.add_view(UserAdmin)
admin.add_view(TaskAdmin)
admin.add_view(TeamAdmin)
admin.add_view(MembershipsAdmin)
admin.add_view(MeetingsAdmin)
admin.add_view(CommentsAdmin)
admin.add_view(EvaluationsAdmin)


@app.get("/")
async def root():
    return RedirectResponse("/ui/login")


if __name__ == "__main__":
    uvicorn.run(app="src.main:app", reload=True)
