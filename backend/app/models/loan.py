from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InterestType, LoanStatus


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    principal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    interest_type: Mapped[InterestType] = mapped_column(Enum(InterestType), nullable=False)
    loan_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    late_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    late_interest_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=0)
    status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus), default=LoanStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="loans")
    partner = relationship("User", back_populates="loans", foreign_keys=[partner_id])
    payments = relationship("Payment", back_populates="loan", cascade="all, delete-orphan")
