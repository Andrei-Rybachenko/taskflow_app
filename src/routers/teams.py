from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from src.auth.schemas import UserRead
from src.auth.users import current_active_user
from src.enums import Role
from src.models import User, TaskORM, MembershipORM, MeetingORM
from src.database import get_async_session
from src.dependencies import admin_required, manager_required, admin_or_manager_required, team_member_required
from src.models.comments import CommentORM
from src.models.evaluations import EvaluationORM
from src.models.teams import TeamORM
from src.schemas import TaskRead, TaskCreate, MembershipCreate, MembershipRead, MembershipUpdate, TaskUpdate, \
    CommentRead, CommentCreate, EvaluationRead, EvaluationCreate, MeetingRead, MeetingCreate
from src.schemas.common_schemas import MembershipShort
from src.schemas.teams import TeamRead, TeamCreate


teams_router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)

@teams_router.post('/',
                   response_model=TeamRead,
                   status_code=status.HTTP_201_CREATED
                   )
async def create_team(team: TeamCreate,
                      current_user: User = Depends(admin_required),
                      db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для создания команды.

    """

    new_team = TeamORM(**team.model_dump(), owner_id=current_user.id)
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)

    return new_team


@teams_router.get("/",
                  response_model=list[TeamRead],
                  status_code=status.HTTP_200_OK)
async def get_teams(_: User = Depends(admin_required),
                    db: AsyncSession = Depends(get_async_session)):
    """

    Ручка возвращает все команды.

    """

    stmt = select(TeamORM).order_by(TeamORM.id)
    result = await db.scalars(stmt)
    teams = result.all()

    return teams


@teams_router.post("/{team_id}/tasks",
                   response_model=TaskRead,
                   status_code=status.HTTP_201_CREATED)

async def create_task(team_id: int,
                      task: TaskCreate,
                      current_user: User = Depends(manager_required),
                      db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для создания задачи.

    """

    new_task = TaskORM(**task.model_dump(),
                       creator_id=current_user.id,
                       team_id=team_id)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@teams_router.post("/{team_id}/members",
                   response_model=MembershipShort,
                   status_code=status.HTTP_201_CREATED)
async def add_member(team_id: int,
                     membership_create: MembershipCreate,
                     _: User = Depends(admin_required),
                     db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для добавления участника в команду.

    """

    stmt = (select(User)
            .where(User.id==membership_create.user_id,
                               User.is_active))

    user = await db.scalar(stmt)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exist")

    stmt = (select(MembershipORM)
            .where(MembershipORM.user_id==membership_create.user_id,
                               MembershipORM.team_id==team_id))

    existing = await db.scalar(stmt)

    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User already in the team")

    new_membership = MembershipORM(**membership_create.model_dump(), team_id=team_id,)
    db.add(new_membership)
    await db.commit()
    await db.refresh(new_membership)

    return new_membership


@teams_router.delete("/{team_id}/members/{user_id}",
                   status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(team_id: int,
                     user_id: int,
                     _: User = Depends(admin_required),
                     db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для удаления участника из команды.

    """

    stmt = select(TeamORM).where(TeamORM.id==team_id)
    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команды не существует."
        )

    stmt = (select(MembershipORM)
            .where(
                    MembershipORM.team_id==team_id,
                    MembershipORM.user_id==user_id
                   )
    )
    membership = await db.scalar(stmt)

    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Участник не состоит в этой команде")

    if membership.role == Role.TEAM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить владельца команды"
        )

    await db.delete(membership)
    await db.commit()


@teams_router.get("/{team_id}/members",
                   response_model=list[MembershipRead],
                   status_code=status.HTTP_200_OK)

async def get_team_members(team_id: int,
                           _: User = Depends(admin_or_manager_required),
                           db: AsyncSession = Depends(get_async_session)):
    """

    Ручка возвращает всех участников команды.

    """

    stmt = (select(MembershipORM)
            .where(MembershipORM.team_id==team_id)
            .options(joinedload(MembershipORM.user)))

    result = await db.scalars(stmt)
    members = result.all()

    return members


@teams_router.patch('/{team_id}/members/{user_id}',
                  response_model=MembershipRead,
                  status_code=status.HTTP_200_OK)

async def change_role(
        team_id: int,
        user_id: int,
        membership_update: MembershipUpdate,
        _: User = Depends(admin_required),
        db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для изменения роли участника в команде.

    """
    stmt = (select(MembershipORM).where(
        MembershipORM.team_id==team_id,
        MembershipORM.user_id==user_id)
            .options(joinedload(MembershipORM.user)))

    membership = await db.scalar(stmt)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="В команде нет такого участника"
    )

    membership.role = membership_update.role

    await db.commit()
    await db.refresh(membership)

    return membership


@teams_router.patch("/{team_id}/tasks/{task_id}",
                  response_model=TaskRead,
                  status_code=status.HTTP_200_OK)
async def update_task(
        team_id: int,
        task_id: int,
        task_update: TaskUpdate,
        current_user: User = Depends(manager_required),
        db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для изменения задачи.

    """

    stmt = select(TeamORM).where(TeamORM.id==team_id)
    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не существует."
        )

    stmt = select(TaskORM).where(TaskORM.id==task_id)
    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не существует."
        )

    await db.execute(
        update(TaskORM)
        .where(TaskORM.id==task_id)
        .values(**task_update.model_dump(exclude_unset=True))
        )

    await db.commit()
    await db.refresh(task)

    return task


@teams_router.get('/{team_id}',
                  response_model=TeamRead,
                  status_code=status.HTTP_200_OK)
async def get_team_by_id(
        team_id: int,
        current_user: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

        Ручка возвращает команду по id.

    """

    stmt = select(TeamORM).where(TeamORM.id==team_id)
    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой команды не существует"
        )

    return team


@teams_router.get('/{team_id}/tasks',
                  response_model=list[TaskRead],
                  status_code=status.HTTP_200_OK)
async def get_tasks_by_team_id(
        team_id: int,
        current_user: User = Depends(manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

        Ручка возвращает задачи команды по id.

    """

    stmt = select(TeamORM).where(TeamORM.id==team_id)
    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой команды не существует"
        )

    stmt = select(TaskORM).where(TaskORM.team_id==team_id)
    result = await db.scalars(stmt)
    tasks = result.all()

    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="У данной команды пока нет задач"
        )

    return tasks


@teams_router.get('/{team_id}/tasks/{task_id}',
                  response_model=TaskRead,
                  status_code=status.HTTP_200_OK)
async def get_task_by_id(
        team_id: int,
        task_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

        Ручка возвращает задачу по id.

    """

    stmt = select(TaskORM).where(
        TaskORM.team_id==team_id,
        TaskORM.id==task_id
    )

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой задачи не существует"
        )

    return task


@teams_router.delete('/{team_id}/tasks/{task_id}',
                  status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_by_id(
        team_id: int,
        task_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

    Ручка удаляет задачу по id.

    """

    stmt = select(TaskORM).where(
        TaskORM.team_id==team_id,
        TaskORM.id==task_id
    )
    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой задачи не существует"
        )

    await db.delete(task)
    await db.commit()


@teams_router.post('/{team_id}/tasks/{task_id}/comments',
                   response_model=CommentRead,
                   status_code=status.HTTP_201_CREATED)
async def add_comment_to_task(
        team_id: int,
        task_id: int,
        comment: CommentCreate,
        current_user: User = Depends(team_member_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(TaskORM)
            .where(TaskORM.id==task_id,
                   TaskORM.team_id==team_id
                   ))
    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    new_comment = CommentORM(**comment.model_dump(),
                             task_id=task_id,
                             author_id=current_user.id)

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    return new_comment


@teams_router.get('/{team_id}/tasks/{task_id}/comments',
                   response_model=list[CommentRead],
                   status_code=status.HTTP_200_OK)
async def get_comments_for_task(
        team_id: int,
        task_id: int,
        current_user: User = Depends(team_member_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(TaskORM)
            .where(TaskORM.id==task_id,
                   TaskORM.team_id==team_id)
            .options(joinedload(TaskORM.comments)))

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    return task.comments


@teams_router.delete('/{team_id}/tasks/{task_id}/comments/{comment_id}',
                  status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_by_id(
        team_id: int,
        task_id: int,
        comment_id: int,
        current_user: User = Depends(team_member_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(CommentORM)
            .join(TaskORM, TaskORM.id==CommentORM.task_id)
            .where(CommentORM.task_id==task_id,
                   CommentORM.id==comment_id,
                   TaskORM.team_id==team_id))

    comment = await db.scalar(stmt)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Комментарий не найден."
        )

    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на удаление комментария."
        )

    await db.delete(comment)
    await db.commit()


@teams_router.post('/{team_id}/tasks/{task_id}/score',
                  response_model=EvaluationRead,
                  status_code=status.HTTP_201_CREATED)
async def add_score_for_task(
        team_id: int,
        task_id: int,
        score: EvaluationCreate,
        current_user: User = Depends(manager_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(TaskORM)
            .where(TaskORM.id==task_id,
                   TaskORM.team_id==team_id))

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    if not task.executor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Задача еще не назначена исполнителю"
        )

    stmt = select(EvaluationORM).where(EvaluationORM.task_id==task_id)
    existing = await db.scalar(stmt)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оценка для задачи уже выставлена."
        )

    task_score = EvaluationORM(**score.model_dump(),
                               task_id=task_id,
                               employee_id=task.executor_id)

    db.add(task_score)
    await db.commit()
    await db.refresh(task_score)

    return task_score



@teams_router.get('/{team_id}/tasks/{task_id}/score',
                  response_model=EvaluationRead,
                  status_code=status.HTTP_200_OK)
async def get_scores_for_task_by_id(
        team_id: int,
        task_id: int,
        current_user: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(TaskORM)
            .where(TaskORM.id == task_id,
                   TaskORM.team_id == team_id)
            .options(joinedload(TaskORM.evaluation)))

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    if not task.evaluation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Оценка для задачи еще не выставлена."
        )
    return task.evaluation


@teams_router.post('/{team_id}/meetings',
                  response_model=MeetingRead,
                  status_code=status.HTTP_201_CREATED)
async def create_meeting(
        team_id: int,
        meeting_data: MeetingCreate,
        current_user: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    new_meeting = MeetingORM(**meeting_data.model_dump(),
                             team_id=team_id)

    db.add(new_meeting)
    await db.commit()
    await db.refresh(new_meeting)

    return new_meeting


@teams_router.get('/{team_id}/meetings',
                  response_model=list[MeetingRead],
                  status_code=status.HTTP_200_OK)
async def get_meetings(
        team_id: int,
        current_user: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = select(MeetingORM).where(MeetingORM.team_id==team_id)
    result = await db.scalars(stmt)
    meetings = result.all()

    return meetings


@teams_router.delete('/{team_id}/meetings/{meeting_id}',
                  status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting_by_id(
        team_id: int,
        meeting_id: int,
        current_user: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(MeetingORM)
            .where(MeetingORM.team_id == team_id,
                   MeetingORM.id==meeting_id))

    meeting = await db.scalar(stmt)

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Встреча не найдена."
        )

    await db.delete(meeting)
    await db.commit()