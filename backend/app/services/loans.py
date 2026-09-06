from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.models.enums import InterestType
from app.models.loan import Loan


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_loan_totals(loan: Loan, today: date | None = None) -> dict:
    today = today or date.today()
    elapsed_days = max((min(today, loan.due_date) - loan.loan_date).days, 0)
    elapsed_months = Decimal(elapsed_days) / Decimal("30")
    rate = Decimal(loan.interest_rate) / Decimal("100")
    principal = Decimal(loan.principal)

    interest = Decimal("0")
    if loan.interest_type in (InterestType.MONTHLY, InterestType.BOTH):
        interest += principal * rate * elapsed_months
    if loan.interest_type in (InterestType.DAILY, InterestType.BOTH):
        interest += principal * rate * Decimal(elapsed_days)

    days_late = max((today - loan.due_date).days, 0)
    late_fee = Decimal(loan.late_fee) if days_late else Decimal("0")
    late_interest = principal * (Decimal(loan.late_interest_rate) / Decimal("100")) * Decimal(days_late)
    paid = sum((Decimal(p.amount) for p in loan.payments), Decimal("0"))
    updated_value = principal + interest
    total_due = max(updated_value + late_fee + late_interest - paid, Decimal("0"))

    return {
        "interest": money(interest),
        "updated_value": money(updated_value),
        "late_fee": money(late_fee),
        "late_interest": money(late_interest),
        "paid": money(paid),
        "total_due": money(total_due),
        "days_late": days_late,
    }
