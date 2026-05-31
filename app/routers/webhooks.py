from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, WebhookSubscription
from app.schemas.api import WebhookCreate, WebhookOut

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("", response_model=list[WebhookOut])
async def list_webhooks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WebhookSubscription]:
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.user_id == user.id)
    )
    return list(result.scalars().all())


@router.post("", response_model=WebhookOut, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    payload: WebhookCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WebhookSubscription:
    hook = WebhookSubscription(
        user_id=user.id,
        url=str(payload.url),
        secret=payload.secret,
    )
    db.add(hook)
    await db.commit()
    await db.refresh(hook)
    return hook


@router.delete("/{hook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    hook_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    hook = await db.get(WebhookSubscription, hook_id)
    if not hook or hook.user_id != user.id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(hook)
    await db.commit()
