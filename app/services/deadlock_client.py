from dataclasses import dataclass

import httpx

from app.config import settings

API_BASE = "https://api.deadlock-api.com/v1"


@dataclass
class LiveMatchSnapshot:
    is_live: bool
    match_id: int | None = None
    hero_id: int | None = None
    hero_name: str | None = None
    duration_seconds: int = 0


def steam_id64_to_account_id(steam_id64: str) -> int:
    return int(steam_id64) - 76561197960265728


class DeadlockClient:
    def __init__(self) -> None:
        self._hero_cache: dict[int, str] = {}

    async def _get_json(self, client: httpx.AsyncClient, url: str) -> object | None:
        headers = {}
        if settings.deadlock_api_key:
            headers["Authorization"] = f"Bearer {settings.deadlock_api_key}"
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None

    async def _ensure_heroes(self, client: httpx.AsyncClient) -> None:
        if self._hero_cache:
            return
        data = await self._get_json(client, f"{API_BASE}/assets/heroes")
        if not isinstance(data, list):
            return
        for hero in data:
            if isinstance(hero, dict) and "id" in hero and "name" in hero:
                self._hero_cache[int(hero["id"])] = str(hero["name"])

    async def get_live_match(self, steam_id64: str) -> LiveMatchSnapshot:
        account_id = steam_id64_to_account_id(steam_id64)
        async with httpx.AsyncClient(timeout=12.0) as client:
            await self._ensure_heroes(client)
            url = f"{API_BASE}/matches/active?account_ids={account_id}"
            data = await self._get_json(client, url)

            if not isinstance(data, list) or not data:
                return LiveMatchSnapshot(is_live=False)

            match = data[0]
            if not isinstance(match, dict):
                return LiveMatchSnapshot(is_live=False)

            players = match.get("players") or []
            player = next(
                (p for p in players if isinstance(p, dict) and p.get("account_id") == account_id),
                None,
            )
            if not player:
                return LiveMatchSnapshot(is_live=False)

            hero_id = int(player.get("hero_id") or 0)
            hero_name = self._hero_cache.get(hero_id, f"Hero #{hero_id}")
            match_id = int(match.get("match_id") or 0)
            duration = int(match.get("duration_s") or 0)

            return LiveMatchSnapshot(
                is_live=True,
                match_id=match_id,
                hero_id=hero_id,
                hero_name=hero_name,
                duration_seconds=duration,
            )
