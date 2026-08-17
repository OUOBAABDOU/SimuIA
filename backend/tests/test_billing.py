import asyncio
import pytest

from app.core.config import Settings
from app.modules.billing.schemas import CheckoutCreate
from app.modules.billing.service import DisabledPaymentProvider, PaymentsNotConfigured


def test_payments_are_disabled_by_default():
    assert Settings().payment_provider == "disabled"


def test_checkout_accepts_only_server_known_plan_codes():
    assert CheckoutCreate(plan_code="pro_monthly").plan_code == "pro_monthly"
    with pytest.raises(ValueError):
        CheckoutCreate(plan_code="custom-price-from-client")


def test_disabled_provider_never_creates_a_checkout():
    with pytest.raises(PaymentsNotConfigured, match="PAYMENTS_NOT_CONFIGURED"):
        asyncio.run(DisabledPaymentProvider().create_checkout(user_id="user", plan_code="pro_monthly"))
