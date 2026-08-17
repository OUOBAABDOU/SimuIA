import hmac
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.candidates.models import User
from app.modules.billing.models import Subscription
from app.modules.billing.schemas import BillingStatus, CheckoutCreate, CheckoutResponse, SubscriptionRead
from app.modules.billing.service import PaymentsNotConfigured, get_payment_provider

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/status", response_model=BillingStatus)
async def billing_status(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    subscription = await db.scalar(
        select(Subscription).where(Subscription.user_id == current_user.id).order_by(Subscription.created_at.desc())
    )
    return BillingStatus(
        enabled=settings.payment_provider != "disabled",
        provider=settings.payment_provider,
        currency=settings.payment_currency.upper(),
        subscription=SubscriptionRead.model_validate(subscription, from_attributes=True) if subscription else None,
    )


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def create_checkout(payload: CheckoutCreate, current_user: User = Depends(get_current_user)):
    try:
        url = await get_payment_provider().create_checkout(user_id=current_user.id, plan_code=payload.plan_code)
    except PaymentsNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return CheckoutResponse(status="created", provider=get_payment_provider().name, checkout_url=url)


@router.post("/webhook")
async def payment_webhook(request: Request):
    settings = get_settings()
    if settings.payment_provider == "disabled":
        raise HTTPException(status_code=503, detail="PAYMENTS_NOT_CONFIGURED")
    body = await request.body()
    signature = request.headers.get("X-Payment-Signature", "")
    expected = hmac.new((settings.payment_webhook_secret or "").encode(), body, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="INVALID_PAYMENT_SIGNATURE")
    raise HTTPException(status_code=501, detail="PAYMENT_PROVIDER_ADAPTER_NOT_CONFIGURED")
