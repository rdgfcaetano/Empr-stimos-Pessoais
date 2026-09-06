from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import InterestType, LoanStatus
from app.schemas.common import ORMModel


class LoanCreate(BaseModel):
    client_id: int
    principal: Decimal = Field(gt=0)
    interest_rate: Decimal = Field(ge=0)
    interest_type: InterestType
    loan_date: date
    due_date: date
    late_fee: Decimal = Field(default=0, ge=0)
    late_interest_rate: Decimal = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.due_date < self.loan_date:
            raise ValueError("A data de vencimento nao pode ser anterior a data do emprestimo")
        return self


class LoanUpdate(BaseModel):
    client_id: int | None = None
    principal: Decimal | None = Field(default=None, gt=0)
    interest_rate: Decimal | None = Field(default=None, ge=0)
    interest_type: InterestType | None = None
    loan_date: date | None = None
    due_date: date | None = None
    late_fee: Decimal | None = Field(default=None, ge=0)
    late_interest_rate: Decimal | None = Field(default=None, ge=0)
    status: LoanStatus | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.loan_date and self.due_date and self.due_date < self.loan_date:
            raise ValueError("A data de vencimento nao pode ser anterior a data do emprestimo")
        return self


class LoanTotals(BaseModel):
    interest: Decimal
    updated_value: Decimal
    late_fee: Decimal
    late_interest: Decimal
    paid: Decimal
    total_due: Decimal
    days_late: int


class LoanOut(ORMModel):
    id: int
    client_id: int
    partner_id: int
    principal: Decimal
    interest_rate: Decimal
    interest_type: InterestType
    loan_date: date
    due_date: date
    late_fee: Decimal
    late_interest_rate: Decimal
    status: LoanStatus
    created_at: datetime
    totals: LoanTotals | None = None
