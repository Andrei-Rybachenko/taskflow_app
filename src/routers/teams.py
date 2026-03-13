from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.models import User
from src.database import get_async_session
from src.dependencies import admin_required
from src.models.teams import TeamORM
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

    new_team = TeamORM(**team.model_dump(), owner_id=current_user.id)
    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)

    return new_team
