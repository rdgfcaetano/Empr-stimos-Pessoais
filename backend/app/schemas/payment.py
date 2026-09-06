from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PaymentCreate(BaseModel):
    paid_at: date
    amount: Decimal = Field(gt=0)
    notes: str | None = None


class PaymentOut(ORMModel):
    id: int
    loan_id: int
    responsible_user_id: int
    responsible_user_name: str | None = None
    paid_at: date
    amount: Decimal
    notes: str | None
    created_at: datetime
