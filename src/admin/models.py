from sqladmin import ModelView

from src.models import TeamORM, MembershipORM, MeetingORM
from src.models.comments import CommentORM
from src.models.evaluations import EvaluationORM
from src.models.users import User
from src.models.tasks import TaskORM


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"

    column_list = [
        User.id,
        User.email,
        User.username,
        User.created_at,
        User.is_superuser,
        User.is_active,
        User.is_verified,
    ]

    form_excluded_columns = [
        User.hashed_password,
        User.email,
        User.created_at,
        User.username,
    ]


class TaskAdmin(ModelView, model=TaskORM):
    name = "Задача"
    name_plural = "Задачи"

    column_list = [
        TaskORM.id,
        TaskORM.title,
        TaskORM.description,
        TaskORM.deadline,
        TaskORM.executor_id,
        TaskORM.created_at,
        TaskORM.status,
    ]


class TeamAdmin(ModelView, model=TeamORM):
    name = "Команда"
    name_plural = "Команды"

    column_list = [TeamORM.id, TeamORM.name,
                   TeamORM.created_at, TeamORM.owner_id]


class MembershipsAdmin(ModelView, model=MembershipORM):
    name = "Участие в команде"
    name_plural = "Участия в командах"

    column_list = [MembershipORM.team_id, MembershipORM.user_id]


class MeetingsAdmin(ModelView, model=MeetingORM):
    name = "Встреча"
    name_plural = "Встречи"

    column_list = [
        MeetingORM.id,
        MeetingORM.team_id,
        MeetingORM.title,
        MeetingORM.creator_id,
        MeetingORM.start_time,
        MeetingORM.end_time,
    ]


class CommentsAdmin(ModelView, model=CommentORM):
    name = "Комментарий"
    name_plural = "Комментарии"

    column_list = [
        CommentORM.id,
        CommentORM.task_id,
        CommentORM.author_id,
        CommentORM.content,
        CommentORM.created_at,
    ]


class EvaluationsAdmin(ModelView, model=EvaluationORM):
    name = "Оценка"
    name_plural = "Оценки"

    column_list = [
        EvaluationORM.id,
        EvaluationORM.task_id,
        EvaluationORM.comment,
        EvaluationORM.employee_id,
        EvaluationORM.created_at,
        EvaluationORM.score,
        EvaluationORM.reviewer_id,
    ]
