from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CheckoutCreate(BaseModel):
    plan_code: str = Field(pattern=r"^(pro_monthly|pro_yearly)$")


class CheckoutResponse(BaseModel):
    status: str
    provider: str
    checkout_url: str | None = None
    message: str | None = None


class SubscriptionRead(BaseModel):
    id: UUID
    plan_code: str
    status: str
    provider: str
    currency: str
    amount_cents: int
    current_period_end: datetime | None


class BillingStatus(BaseModel):
    enabled: bool
    provider: str
    currency: str
    subscription: SubscriptionRead | None = None
