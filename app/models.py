from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    watches: Mapped[list["WatchTarget"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    webhooks: Mapped[list["WebhookSubscription"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class WatchTarget(Base):
    __tablename__ = "watch_targets"
    __table_args__ = (UniqueConstraint("user_id", "steam_id64", name="uq_user_steam"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    steam_id64: Mapped[str] = mapped_column(String(20), index=True)
    label: Mapped[str] = mapped_column(String(120), default="")
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)
    last_match_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_hero_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_hero_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="watches")
    events: Mapped[list["MatchEvent"]] = relationship(back_populates="watch", cascade="all, delete-orphan")


class MatchEvent(Base):
    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watch_id: Mapped[int] = mapped_column(ForeignKey("watch_targets.id", ondelete="CASCADE"), index=True)
    match_id: Mapped[int] = mapped_column(Integer, index=True)
    hero_id: Mapped[int] = mapped_column(Integer, default=0)
    hero_name: Mapped[str] = mapped_column(String(80), default="Unknown")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    event_type: Mapped[str] = mapped_column(String(32), default="match_started")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    watch: Mapped["WatchTarget"] = relationship(back_populates="events")


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    secret: Mapped[str] = mapped_column(String(64), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="webhooks")
