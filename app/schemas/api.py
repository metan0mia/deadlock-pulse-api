from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WatchCreate(BaseModel):
    steam_id64: str = Field(min_length=17, max_length=20, pattern=r"^\d+$")
    label: str = Field(default="", max_length=120)


class WatchOut(BaseModel):
    id: int
    steam_id64: str
    label: str
    is_live: bool
    last_match_id: int | None
    last_hero_id: int | None
    last_hero_name: str | None
    last_checked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchEventOut(BaseModel):
    id: int
    watch_id: int
    match_id: int
    hero_id: int
    hero_name: str
    duration_seconds: int
    event_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookCreate(BaseModel):
    url: HttpUrl
    secret: str = Field(default="", max_length=64)


class WebhookOut(BaseModel):
    id: int
    url: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class HeroStat(BaseModel):
    hero_name: str
    live_sessions: int
    unique_players: int


class PulseStatus(BaseModel):
    service: str
    version: str
    watches_total: int
    watches_live: int
    events_last_24h: int
    poll_interval_seconds: int
