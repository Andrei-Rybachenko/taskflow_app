from collections import defaultdict
from datetime import datetime, timedelta
import calendar as calendar_module

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status as http_status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from src.auth.schemas import UserCreate
from src.auth.users import auth_backend, get_user_manager
from src.database import get_async_session
from src.dependencies import (
    admin_or_manager_required,
    admin_required,
    manager_required,
    memberships_service,
    meetings_service,
    users_service,
    tasks_service,
    team_member_required,
    teams_service,
    comments_service,
    evaluations_service,
)
from sqlalchemy import select, extract, func as sa_func
from src.models import User
from src.routers import current_active_user, current_optional_user
from src.schemas import MeetingCreate, TaskCreate, CommentCreate, EvaluationCreate, MembershipCreate
from src.schemas.teams import TeamCreate
from src.services.meetings_service import MeetingsService
from src.services.tasks_service import TasksService
from src.services.teams_service import TeamsService
from src.services.users_service import UsersService
from src.services.memberships_service import MembershipsService
from src.services.comments_service import CommentsService
from src.services.evaluations_service import EvaluationsService
from src.enums import Role


web_router = APIRouter(prefix="/ui")
templates = Jinja2Templates(directory="templates")


@web_router.get("/", response_class=RedirectResponse)
async def ui_index(
    user: User | None = Depends(current_optional_user),
):
    return RedirectResponse("/ui/teams" if user else "/ui/login", status_code=303)



@web_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "user": None})


@web_router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_manager = Depends(get_user_manager),
):
    user = await user_manager.authenticate(form_data)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "user": None, "error": "Неверный логин или пароль"},
        )

    strategy = auth_backend.get_strategy()
    token = await strategy.write_token(user)

    response = RedirectResponse("/ui/teams", status_code=303)
    response.set_cookie(
        key="auth",
        value=token,
        max_age=strategy.lifetime_seconds,
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return response


@web_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "user": None})


@web_router.post("/register")
async def register(
    request: Request,
    user_manager=Depends(get_user_manager),
):
    form = await request.form()
    email = (form.get("email") or "").strip()
    username = (form.get("username") or "").strip()
    password = form.get("password") or ""

    try:
        user = await user_manager.create(UserCreate(email=email, username=username, password=password))
    except Exception:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "user": None,
                "error": "Не удалось зарегистрироваться. Проверьте данные или попробуйте другой email и имя пользователя.",
            },
        )

    strategy = auth_backend.get_strategy()
    token = await strategy.write_token(user)
    response = RedirectResponse("/ui/teams", status_code=303)
    response.set_cookie(
        key="auth",
        value=token,
        max_age=strategy.lifetime_seconds,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response

@web_router.get("/logout")
async def logout():
    response = RedirectResponse("/ui/login", status_code=303)
    response.delete_cookie("auth")
    return response


@web_router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: User = Depends(current_active_user),
    m_service: MembershipsService = Depends(memberships_service),
):
    memberships = await m_service.get_user_memberships(user.id)
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "memberships": memberships},
    )


@web_router.post("/profile/delete", response_class=RedirectResponse)
async def delete_my_profile(
    service: UsersService = Depends(users_service),
    user: User = Depends(current_active_user),
):
    await service.deactivate_me(user.id)
    response = RedirectResponse("/ui/login", status_code=303)
    response.delete_cookie("auth")
    return response



@web_router.get("/teams")
async def list_teams(
        request: Request,
        service: TeamsService = Depends(teams_service),
        user: User = Depends(current_active_user),
        page: int = 1,
        size: int = 10,
):
    size = max(1, min(size, 50))
    page = max(page, 1)
    offset = (page - 1) * size

    # Берем на 1 больше, чтобы понять есть ли next
    teams = (
        await service.get_teams(limit=size + 1, offset=offset)
        if user.is_superuser
        else await service.get_user_teams(user.id, limit=size + 1, offset=offset)
    )
    has_next = len(teams) > size
    teams = teams[:size]

    return templates.TemplateResponse(
        "teams.html",
        {
            "request": request,
            "teams": teams,
            "user": user,
            "page": page,
            "size": size,
            "has_prev": page > 1,
            "has_next": has_next,
        },
    )


@web_router.post("/teams/create")
async def create_team(
    request: Request,
    service: TeamsService = Depends(teams_service),
    m_service: MembershipsService = Depends(memberships_service),
    user: User = Depends(admin_required),
):
    form = await request.form()
    name = form.get("name")

    team_data = TeamCreate(name=name)
    new_team = await service.create(team_data, owner_id=user.id)

    member_ids = form.getlist("member_ids")
    for uid_str in member_ids:
        try:
            uid = int(uid_str)
            role_str = form.get(f"member_role_{uid}") or "employee"
            try:
                role = Role(role_str)
            except ValueError:
                role = Role.EMPLOYEE
            await m_service.add_member(MembershipCreate(
                user_id=uid,
                team_id=new_team.id,
                role=role,
            ))
        except Exception:
            pass

    return RedirectResponse("/ui/teams", status_code=303)


@web_router.get("/teams/create")
async def create_team_page(
    request: Request,
    u_service: UsersService = Depends(users_service),
    user: User = Depends(admin_required),
):
    all_users = await u_service.get_users()
    return templates.TemplateResponse("create_team.html", {
        "request": request,
        "user": user,
        "users": all_users,
    })


@web_router.get("/teams/{team_id}")
async def team_detail(
    request: Request,
    team_id: int,
    team_service: TeamsService = Depends(teams_service),
    task_service: TasksService = Depends(tasks_service),
    meeting_service: MeetingsService = Depends(meetings_service),
    m_service: MembershipsService = Depends(memberships_service),
    u_service: UsersService = Depends(users_service),
    user: User = Depends(team_member_required),
    page_tasks: int = 1,
    page_meetings: int = 1,
    size: int = 10,
):
    team = await team_service.get_team(team_id)
    tasks = []
    meetings = []
    error_tasks = None
    error_meetings = None
    try:
        size = max(1, min(size, 50))
        page_tasks = max(page_tasks, 1)
        offset_tasks = (page_tasks - 1) * size
        tasks = await task_service.get_team_tasks(team_id, limit=size + 1, offset=offset_tasks)
    except Exception as e:
        error_tasks = str(e)
    try:
        page_meetings = max(page_meetings, 1)
        offset_meetings = (page_meetings - 1) * size
        meetings = await meeting_service.get_team_meetings(team_id, limit=size + 1, offset=offset_meetings)
    except Exception as e:
        error_meetings = str(e)

    has_next_tasks = len(tasks) > size if isinstance(tasks, list) else False
    has_next_meetings = len(meetings) > size if isinstance(meetings, list) else False
    if isinstance(tasks, list):
        tasks = tasks[:size]
    if isinstance(meetings, list):
        meetings = meetings[:size]

    members = await m_service.get_members(team_id)
    member_user_ids = {m.user_id for m in members}
    all_users = await u_service.get_users()
    available_users = [u for u in all_users if u.id not in member_user_ids] if user.is_superuser else []

    return templates.TemplateResponse("team_detail.html", {
        "request": request,
        "user": user,
        "team": team,
        "tasks": tasks,
        "meetings": meetings,
        "error_tasks": error_tasks,
        "error_meetings": error_meetings,
        "page_tasks": page_tasks,
        "page_meetings": page_meetings,
        "size": size,
        "has_prev_tasks": page_tasks > 1,
        "has_next_tasks": has_next_tasks,
        "has_prev_meetings": page_meetings > 1,
        "has_next_meetings": has_next_meetings,
        "members": members,
        "available_users": available_users,
    })


@web_router.post("/teams/{team_id}/members/add", response_class=RedirectResponse)
async def add_team_member(
    team_id: int,
    request: Request,
    m_service: MembershipsService = Depends(memberships_service),
    _: User = Depends(admin_required),
):
    form = await request.form()
    user_id_str = form.get("user_id")
    role_str = form.get("role") or "employee"
    if user_id_str:
        try:
            uid = int(user_id_str)
            try:
                role = Role(role_str)
            except ValueError:
                role = Role.EMPLOYEE
            await m_service.add_member(MembershipCreate(
                user_id=uid,
                team_id=team_id,
                role=role,
            ))
        except Exception:
            pass
    return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)


@web_router.post("/teams/{team_id}/members/{member_user_id}/delete", response_class=RedirectResponse)
async def remove_team_member(
    team_id: int,
    member_user_id: int,
    m_service: MembershipsService = Depends(memberships_service),
    _: User = Depends(admin_required),
):
    await m_service.delete(member_user_id, team_id)
    return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)


@web_router.get("/teams/{team_id}/tasks/create")
async def create_task_page(
    request: Request,
    team_id: int,
    user: User = Depends(manager_required),
):
    return templates.TemplateResponse("create_task.html", {
        "request": request,
        "user": user,
        "team_id": team_id
    })


@web_router.post("/teams/{team_id}/tasks/create")
async def create_task(
    request: Request,
    team_id: int,
    task_service: TasksService = Depends(tasks_service),
    user: User = Depends(manager_required),
):
    form = await request.form()

    title = form.get("title")
    description = form.get("description")
    deadline_str = form.get("deadline")

    deadline = datetime.fromisoformat(deadline_str) if deadline_str else None

    task_data = TaskCreate(
        title=title,
        description=description,
        deadline=deadline,
        team_id=team_id,
    )

    await task_service.create(task_data, creator_id=user.id)

    return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)


@web_router.get("/teams/{team_id}/tasks/{task_id}", response_class=HTMLResponse)
async def task_detail_page(
    request: Request,
    team_id: int,
    task_id: int,
    task_service: TasksService = Depends(tasks_service),
    user: User = Depends(team_member_required),
    c_service: CommentsService = Depends(comments_service),
    m_service: MembershipsService = Depends(memberships_service),
):
    task = await task_service.get_task_with_relations_or_404(task_id)
    if task.team_id != team_id:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    comments = await c_service.get_comments(task_id, team_id)
    membership = await m_service.get(user.id, team_id)
    is_manager = user.is_superuser or (
        membership is not None
        and membership.role in (Role.MANAGER, Role.TEAM_ADMIN)
    )
    has_evaluation = task.evaluation is not None

    return templates.TemplateResponse(
        "task_detail_page.html",
        {
            "request": request,
            "user": user,
            "team_id": team_id,
            "task": task,
            "comments": comments,
            "is_manager": is_manager,
            "has_evaluation": has_evaluation,
        },
    )


@web_router.post("/teams/{team_id}/tasks/{task_id}/comment", response_class=RedirectResponse)
async def add_task_comment_ui(
    team_id: int,
    task_id: int,
    request: Request,
    user: User = Depends(team_member_required),
    c_service: CommentsService = Depends(comments_service),
):
    form = await request.form()
    content = (form.get("content") or "").strip()
    if content:
        comment = CommentCreate(task_id=task_id, content=content)
        await c_service.create_comment(comment, user.id, team_id)
    return RedirectResponse(f"/ui/teams/{team_id}/tasks/{task_id}", status_code=303)


@web_router.post("/teams/{team_id}/tasks/{task_id}/evaluate", response_class=RedirectResponse)
async def add_task_evaluation_ui(
    team_id: int,
    task_id: int,
    request: Request,
    user: User = Depends(manager_required),
    e_service: EvaluationsService = Depends(evaluations_service),
    task_service: TasksService = Depends(tasks_service),
):
    task = await task_service.get_task_or_404(task_id)
    if task.team_id != team_id:
        return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)

    form = await request.form()
    score_raw = form.get("score")
    comment_text = (form.get("comment") or "").strip() or None
    if score_raw is None or task.executor_id is None:
        return RedirectResponse(f"/ui/teams/{team_id}/tasks/{task_id}", status_code=303)

    score = int(score_raw)
    await e_service.create(
        EvaluationCreate(
            score=score,
            employee_id=task.executor_id,
            comment=comment_text,
        ),
        task_id,
        user.id,
        team_id,
    )
    return RedirectResponse(f"/ui/teams/{team_id}/tasks/{task_id}", status_code=303)


@web_router.post("/teams/{team_id}/delete", response_class=RedirectResponse)
async def delete_team(
    team_id: int,
    service: TeamsService = Depends(teams_service),
    _: User = Depends(admin_required),
):
    await service.delete_team(team_id)
    return RedirectResponse("/ui/teams", status_code=303)


@web_router.post("/teams/{team_id}/tasks/{task_id}/delete", response_class=RedirectResponse)
async def delete_task(
    team_id: int,
    task_id: int,
    task_service: TasksService = Depends(tasks_service),
    user: User = Depends(current_active_user),
    m_service: MembershipsService = Depends(memberships_service),
):
    task = await task_service.get_task_or_404(task_id)
    if task.team_id != team_id:
        return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)

    if user.is_superuser or task.creator_id == user.id:
        await task_service.delete(task_id)
        return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)

    membership = await m_service.get(user.id, team_id)
    if membership and membership.role in (Role.MANAGER, Role.TEAM_ADMIN):
        await task_service.delete(task_id)
        return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)

    raise HTTPException(
        status_code=http_status.HTTP_403_FORBIDDEN, detail="Недостаточно прав."
    )


@web_router.post("/teams/{team_id}/meetings/{meeting_id}/delete", response_class=RedirectResponse)
async def delete_meeting(
    team_id: int,
    meeting_id: int,
    service: MeetingsService = Depends(meetings_service),
    _: User = Depends(admin_or_manager_required),
):
    meeting = await service.get_meeting(meeting_id)
    if meeting.team_id != team_id:
        return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)

    await service.delete_meeting(meeting_id, team_id)
    return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)


@web_router.get("/tasks")
async def all_tasks_page(
    request: Request,
    task_service: TasksService = Depends(tasks_service),
    user: User = Depends(current_active_user),
    page: int = 1,
    size: int = 10,
):
    size = max(1, min(size, 50))
    page = max(page, 1)
    offset = (page - 1) * size
    tasks = await task_service.get_users_tasks(user.id, limit=size + 1, offset=offset)
    has_next = len(tasks) > size
    tasks = tasks[:size]
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "tasks": tasks,
        "user": user
        ,
        "page": page,
        "size": size,
        "has_prev": page > 1,
        "has_next": has_next,
    })


@web_router.get("/teams/{team_id}/meetings/create", response_class=HTMLResponse)
async def create_meeting_page(
    request: Request,
    team_id: int,
    user: User = Depends(admin_or_manager_required),
):
    return templates.TemplateResponse(
        "create_meeting.html",
        {"request": request, "user": user, "team_id": team_id},
    )


@web_router.post("/teams/{team_id}/meetings/create", response_class=RedirectResponse)
async def create_meeting(
    request: Request,
    team_id: int,
    service: MeetingsService = Depends(meetings_service),
    user: User = Depends(admin_or_manager_required),
):
    form = await request.form()
    title = form.get("title")
    start_time = datetime.fromisoformat(form.get("start_time"))
    end_time = datetime.fromisoformat(form.get("end_time"))

    await service.create(
        MeetingCreate(title=title, start_time=start_time, end_time=end_time, team_id=team_id),
        creator_id=user.id,
    )
    return RedirectResponse(f"/ui/teams/{team_id}", status_code=303)

# Календарь

_MONTH_NAMES_RU = (
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
)


@web_router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(
    request: Request,
    user: User = Depends(current_active_user),
    view: str = "month",
    year: str = None,
    month: str = None,
    date: str = None,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        year = int(year) if year else None
    except (ValueError, TypeError):
        year = None
    try:
        month = int(month) if month else None
    except (ValueError, TypeError):
        month = None
    from src.models import TaskORM, MeetingORM

    today = datetime.today().date()

    if view == "day":
        try:
            current_date = datetime.strptime(date, "%Y-%m-%d").date() if date else today
        except (ValueError, TypeError):
            current_date = today

        prev_date = current_date - timedelta(days=1)
        next_date = current_date + timedelta(days=1)

        tasks_q = await db.scalars(
            select(TaskORM).where(sa_func.date(TaskORM.deadline) == current_date)
        )
        day_tasks = tasks_q.all()

        meetings_q = await db.scalars(
            select(MeetingORM).where(sa_func.date(MeetingORM.start_time) == current_date)
        )
        day_meetings = meetings_q.all()

        return templates.TemplateResponse("calendar.html", {
            "request": request,
            "user": user,
            "view": "day",
            "today": str(today),
            "current_date": str(current_date),
            "date_display": current_date.strftime("%d.%m.%Y"),
            "prev_date": str(prev_date),
            "next_date": str(next_date),
            "day_tasks": sorted(day_tasks, key=lambda t: t.deadline),
            "day_meetings": sorted(day_meetings, key=lambda m: m.start_time),
        })

    else:
        y = year or today.year
        m = month or today.month

        prev_month_date = (datetime(y, m, 1) - timedelta(days=1)).replace(day=1)
        next_month_date = (datetime(y, m, 28) + timedelta(days=4)).replace(day=1)

        tasks_q = await db.scalars(
            select(TaskORM).where(
                extract("year", TaskORM.deadline) == y,
                extract("month", TaskORM.deadline) == m,
            )
        )
        tasks_by_day = defaultdict(list)
        for t in tasks_q.all():
            tasks_by_day[t.deadline.day].append(t)

        meetings_q = await db.scalars(
            select(MeetingORM).where(
                extract("year", MeetingORM.start_time) == y,
                extract("month", MeetingORM.start_time) == m,
            )
        )
        meetings_by_day = defaultdict(list)
        for mt in meetings_q.all():
            meetings_by_day[mt.start_time.day].append(mt)

        weeks = calendar_module.monthcalendar(y, m)

        return templates.TemplateResponse("calendar.html", {
            "request": request,
            "user": user,
            "view": "month",
            "today": str(today),
            "today_day": today.day,
            "today_month": today.month,
            "today_year": today.year,
            "year": y,
            "month": m,
            "month_name": _MONTH_NAMES_RU[m],
            "prev_year": prev_month_date.year,
            "prev_month": prev_month_date.month,
            "next_year": next_month_date.year,
            "next_month": next_month_date.month,
            "weeks": weeks,
            "tasks_by_day": dict(tasks_by_day),
            "meetings_by_day": dict(meetings_by_day),
        })
