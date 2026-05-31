from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import MatchEvent, User, WatchTarget
from app.schemas.api import HeroStat, PulseStatus

router = APIRouter(tags=["analytics"])


@router.get("/status", response_model=PulseStatus)
async def pulse_status(db: AsyncSession = Depends(get_db)) -> PulseStatus:
    watches_total = await db.scalar(select(func.count()).select_from(WatchTarget)) or 0
    watches_live = await db.scalar(
        select(func.count()).select_from(WatchTarget).where(WatchTarget.is_live.is_(True))
    ) or 0

    since = datetime.now(UTC) - timedelta(hours=24)
    events_last_24h = await db.scalar(
        select(func.count()).select_from(MatchEvent).where(MatchEvent.created_at >= since)
    ) or 0

    return PulseStatus(
        service="Deadlock Pulse API",
        version="1.0.0",
        watches_total=watches_total,
        watches_live=watches_live,
        events_last_24h=events_last_24h,
        poll_interval_seconds=settings.poll_interval_seconds,
    )


@router.get("/analytics/heroes", response_model=list[HeroStat])
async def hero_analytics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[HeroStat]:
    """Raw SQL analytics — top heroes among your watched players."""
    query = text(
        """
        SELECT
            me.hero_name AS hero_name,
            COUNT(*) AS live_sessions,
            COUNT(DISTINCT wt.steam_id64) AS unique_players
        FROM match_events me
        INNER JOIN watch_targets wt ON wt.id = me.watch_id
        WHERE wt.user_id = :user_id
        GROUP BY me.hero_name
        ORDER BY live_sessions DESC
        LIMIT 10
        """
    )
    result = await db.execute(query, {"user_id": user.id})
    rows = result.mappings().all()
    return [
        HeroStat(
            hero_name=row["hero_name"],
            live_sessions=int(row["live_sessions"]),
            unique_players=int(row["unique_players"]),
        )
        for row in rows
    ]
