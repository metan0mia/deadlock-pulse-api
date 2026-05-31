from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import MatchEvent, User, WatchTarget
from app.schemas.api import MatchEventOut

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[MatchEventOut])
async def list_events(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MatchEvent]:
    result = await db.execute(
        select(MatchEvent)
        .join(WatchTarget, WatchTarget.id == MatchEvent.watch_id)
        .where(WatchTarget.user_id == user.id)
        .order_by(MatchEvent.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
