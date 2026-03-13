import enum


class TaskStatus(str, enum.Enum):
    """
    Вспомогательный enum-класс
    """
    OPEN = "открыто"
    IN_PROGRESS = "в работе"
    FINISHED = "выполнено"


class Role(str, enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    TEAM_ADMIN = "team_admin"