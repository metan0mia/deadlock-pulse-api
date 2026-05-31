import hashlib
import hmac
import json
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MatchEvent, User, WatchTarget, WebhookSubscription


async def dispatch_webhooks(
    db: AsyncSession,
    user_id: int,
    event_type: str,
    payload: dict,
) -> int:
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.user_id == user_id,
            WebhookSubscription.is_active.is_(True),
        )
    )
    hooks = result.scalars().all()
    if not hooks:
        return 0

    body = {
        "event": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": payload,
    }
    raw = json.dumps(body, ensure_ascii=False)
    sent = 0

    async with httpx.AsyncClient(timeout=8.0) as client:
        for hook in hooks:
            headers = {"Content-Type": "application/json", "User-Agent": "DeadlockPulse/1.0"}
            if hook.secret:
                signature = hmac.new(hook.secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
                headers["X-Pulse-Signature"] = signature
            try:
                response = await client.post(hook.url, content=raw, headers=headers)
                if response.status_code < 500:
                    sent += 1
            except httpx.HTTPError:
                continue

    return sent


async def record_match_started(
    db: AsyncSession,
    watch: WatchTarget,
    match_id: int,
    hero_id: int,
    hero_name: str,
    duration_seconds: int,
) -> MatchEvent:
    event = MatchEvent(
        watch_id=watch.id,
        match_id=match_id,
        hero_id=hero_id,
        hero_name=hero_name,
        duration_seconds=duration_seconds,
        event_type="match_started",
        payload_json=json.dumps(
            {
                "steam_id64": watch.steam_id64,
                "label": watch.label,
                "match_id": match_id,
                "hero_name": hero_name,
            }
        ),
    )
    db.add(event)
    watch.is_live = True
    watch.last_match_id = match_id
    watch.last_hero_id = hero_id
    watch.last_hero_name = hero_name
    watch.last_checked_at = datetime.now(UTC)

    user = await db.get(User, watch.user_id)
    if user:
        await dispatch_webhooks(
            db,
            user.id,
            "match_started",
            {
                "watch_id": watch.id,
                "steam_id64": watch.steam_id64,
                "label": watch.label,
                "match_id": match_id,
                "hero_name": hero_name,
                "duration_seconds": duration_seconds,
            },
        )

    return event
