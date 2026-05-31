import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import WatchTarget
from app.services.deadlock_client import DeadlockClient
from app.services.webhook_dispatcher import record_match_started

logger = logging.getLogger("pulse.poller")
client = DeadlockClient()
_task: asyncio.Task | None = None


async def poll_once() -> int:
    updated = 0
    async with SessionLocal() as db:
        result = await db.execute(select(WatchTarget))
        watches = result.scalars().all()

        for watch in watches:
            snapshot = await client.get_live_match(watch.steam_id64)
            watch.last_checked_at = datetime.now(UTC)

            if snapshot.is_live and snapshot.match_id and watch.last_match_id != snapshot.match_id:
                await record_match_started(
                    db,
                    watch,
                    snapshot.match_id,
                    snapshot.hero_id or 0,
                    snapshot.hero_name or "Unknown",
                    snapshot.duration_seconds,
                )
                updated += 1
                logger.info(
                    "Live match detected: watch=%s steam=%s match=%s hero=%s",
                    watch.id,
                    watch.steam_id64,
                    snapshot.match_id,
                    snapshot.hero_name,
                )
            elif snapshot.is_live:
                watch.is_live = True
                watch.last_match_id = snapshot.match_id
                watch.last_hero_id = snapshot.hero_id
                watch.last_hero_name = snapshot.hero_name
            else:
                watch.is_live = False

        await db.commit()

    return updated


async def _poll_loop() -> None:
    while True:
        try:
            count = await poll_once()
            if count:
                logger.info("Poll cycle complete, new events: %s", count)
        except Exception:
            logger.exception("Poll cycle failed")
        await asyncio.sleep(settings.poll_interval_seconds)


def start_poller() -> None:
    global _task
    if not settings.enable_poller:
        logger.info("Background poller disabled (ENABLE_POLLER=false)")
        return
    if _task and not _task.done():
        return
    _task = asyncio.create_task(_poll_loop())
    logger.info("Background poller started (interval=%ss)", settings.poll_interval_seconds)


def stop_poller() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
    _task = None
