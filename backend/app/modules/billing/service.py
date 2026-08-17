from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.config import get_settings


class PaymentsNotConfigured(RuntimeError):
    """Raised while the application is intentionally in payment-disabled mode."""


class PaymentProvider(Protocol):
    name: str

    async def create_checkout(self, *, user_id: UUID, plan_code: str) -> str:
        ...


@dataclass(frozen=True)
class DisabledPaymentProvider:
    name: str = "disabled"

    async def create_checkout(self, *, user_id: UUID, plan_code: str) -> str:
        raise PaymentsNotConfigured("PAYMENTS_NOT_CONFIGURED")


def get_payment_provider() -> PaymentProvider:
    settings = get_settings()
    if settings.payment_provider == "disabled":
        return DisabledPaymentProvider()
    # The provider boundary is ready; a provider adapter is enabled only after
    # credentials and webhook verification have been configured.
    raise PaymentsNotConfigured("PAYMENT_PROVIDER_ADAPTER_NOT_CONFIGURED")
