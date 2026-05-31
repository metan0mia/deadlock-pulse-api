from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, WatchTarget
from app.schemas.api import WatchCreate, WatchOut

router = APIRouter(prefix="/watches", tags=["watches"])


@router.get("", response_model=list[WatchOut])
async def list_watches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WatchTarget]:
    result = await db.execute(select(WatchTarget).where(WatchTarget.user_id == user.id))
    return list(result.scalars().all())


@router.post("", response_model=WatchOut, status_code=status.HTTP_201_CREATED)
async def add_watch(
    payload: WatchCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WatchTarget:
    existing = await db.execute(
        select(WatchTarget).where(
            WatchTarget.user_id == user.id,
            WatchTarget.steam_id64 == payload.steam_id64,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Steam ID already on watch list")

    watch = WatchTarget(user_id=user.id, steam_id64=payload.steam_id64, label=payload.label)
    db.add(watch)
    await db.commit()
    await db.refresh(watch)
    return watch


@router.delete("/{watch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watch(
    watch_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    watch = await db.get(WatchTarget, watch_id)
    if not watch or watch.user_id != user.id:
        raise HTTPException(status_code=404, detail="Watch not found")
    await db.delete(watch)
    await db.commit()
