from decimal import Decimal

from pydantic import BaseModel


class DashboardOut(BaseModel):
    total_loaned: Decimal
    total_received: Decimal
    profit: Decimal
    client_count: int
    active_loan_count: int
    overdue_count: int
    monthly: list[dict]
