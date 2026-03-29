import calendar
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select, extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import PlainTextResponse

from src.database import get_async_session
from src.models import TaskORM, MeetingORM

calendar_router = APIRouter(prefix="/calendar", tags=["Календарь"])

_MONTH_NAMES_RU = (
    "",
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)


@calendar_router.get("/month", response_class=PlainTextResponse)
async def get_month_calendar(
    year: int, month: int, db: AsyncSession = Depends(get_async_session)
):

    events_per_day = defaultdict(int)

    tasks_stmt = select(TaskORM.deadline).where(
        extract("year", TaskORM.deadline) == year,
        extract("month", TaskORM.deadline) == month,
    )

    tasks = (await db.scalars(tasks_stmt)).all()

    for d in tasks:
        events_per_day[d.day] += 1

    meetings_stmt = select(MeetingORM.start_time).where(
        extract("year", MeetingORM.start_time) == year,
        extract("month", MeetingORM.start_time) == month,
    )

    meetings = (await db.scalars(meetings_stmt)).all()

    for d in meetings:
        events_per_day[d.day] += 1

    cal = calendar.monthcalendar(year, month)

    lines = [
        f"{_MONTH_NAMES_RU[month]} {year}\n",
        "Пн Вт Ср Чт Пт Сб Вс",
    ]

    for week in cal:
        row = []

        for day in week:
            if day == 0:
                row.append("   ")

            else:
                count = events_per_day.get(day, 0)

                if count > 0:
                    cell = f"{day}({count})"
                else:
                    cell = f"{day}"

                row.append(cell.rjust(3))

        lines.append(" ".join(row))

    return "\n".join(lines)


@calendar_router.get("/day", response_class=PlainTextResponse)
async def get_day_calendar(
    calendar_date: date, db: AsyncSession = Depends(get_async_session)
):

    tasks = (
        await db.scalars(
            select(TaskORM)
            .where(func.date(TaskORM.deadline) == calendar_date)
        )
    ).all()

    meetings = (
        await db.scalars(
            select(MeetingORM)
            .where(func.date(MeetingORM.start_time) == calendar_date)
        )
    ).all()

    lines = [f"{calendar_date}\n", "Задачи:"]

    if tasks:
        for t in tasks:
            lines.append(f"  • {t.title}")
    else:
        lines.append("  —")

    lines.append("\nВстречи:")
    if meetings:
        for m in meetings:
            lines.append(f"  • {m.title}")
    else:
        lines.append("  —")

    return "\n".join(lines)
