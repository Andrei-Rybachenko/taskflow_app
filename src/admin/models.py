from sqladmin import ModelView

from src.models import TeamORM, MembershipORM, MeetingORM
from src.models.comments import CommentORM
from src.models.evaluations import EvaluationORM
from src.models.users import User
from src.models.tasks import TaskORM


class UserAdmin(ModelView, model=User):
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
    column_list = [
        TaskORM.id,
        TaskORM.title,
        TaskORM.description,
        TaskORM.deadline,
        TaskORM.executor_id,
        TaskORM.created_at,
        TaskORM.status,
    ]

    name_plural = "Tasks"


class TeamAdmin(ModelView, model=TeamORM):
    column_list = [TeamORM.id, TeamORM.name,
                   TeamORM.created_at, TeamORM.owner_id]

    name_plural = "Teams"


class MembershipsAdmin(ModelView, model=MembershipORM):
    column_list = [MembershipORM.team_id, MembershipORM.user_id]

    name_plural = "Memberships"


class MeetingsAdmin(ModelView, model=MeetingORM):
    column_list = [
        MeetingORM.id,
        MeetingORM.team_id,
        MeetingORM.title,
        MeetingORM.creator_id,
        MeetingORM.start_time,
        MeetingORM.end_time,
    ]

    name_plural = "Meetings"


class CommentsAdmin(ModelView, model=CommentORM):
    column_list = [
        CommentORM.id,
        CommentORM.task_id,
        CommentORM.author_id,
        CommentORM.content,
        CommentORM.created_at,
    ]

    name_plural = "Comments"


class EvaluationsAdmin(ModelView, model=EvaluationORM):
    column_list = [
        EvaluationORM.id,
        EvaluationORM.task_id,
        EvaluationORM.comment,
        EvaluationORM.employee_id,
        EvaluationORM.created_at,
        EvaluationORM.score,
        EvaluationORM.reviewer_id,
    ]

    name_plural = "Evaluation"
