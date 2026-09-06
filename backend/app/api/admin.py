from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.audit import AuditLog, Notification
from app.models.client import Client
from app.models.enums import LoanStatus, UserRole
from app.models.loan import Loan
from app.models.payment import Payment
from app.models.user import User
from app.schemas.audit import AuditLogOut, NotificationOut
from app.schemas.dashboard import DashboardOut
from app.services.loans import calculate_loan_totals

router = APIRouter(tags=["admin"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loans_query = db.query(Loan)
    clients_query = db.query(Client)
    payments_query = db.query(Payment)
    if current_user.role != UserRole.ADMIN:
        loans_query = loans_query.filter(Loan.partner_id == current_user.id)
        clients_query = clients_query.filter(Client.partner_id == current_user.id)
        payments_query = payments_query.join(Loan).filter(Loan.partner_id == current_user.id)

    loans = loans_query.all()
    total_loaned = sum((Decimal(l.principal) for l in loans), Decimal("0"))
    total_received = payments_query.with_entities(func.coalesce(func.sum(Payment.amount), 0)).scalar()
    overdue_count = sum(1 for loan in loans if calculate_loan_totals(loan)["days_late"] and loan.status != LoanStatus.PAID)
    active = sum(1 for loan in loans if loan.status == LoanStatus.OPEN)
    monthly_map = defaultdict(lambda: {"loaned": Decimal("0"), "received": Decimal("0")})
    for loan in loans:
        key = loan.loan_date.strftime("%Y-%m")
        monthly_map[key]["loaned"] += Decimal(loan.principal)
    payment_rows = payments_query.all()
    for payment in payment_rows:
        key = payment.paid_at.strftime("%Y-%m")
        monthly_map[key]["received"] += Decimal(payment.amount)
    monthly = [
        {"month": month, "loaned": values["loaned"], "received": values["received"]}
        for month, values in sorted(monthly_map.items())
    ]
    return DashboardOut(
        total_loaned=total_loaned,
        total_received=Decimal(total_received or 0),
        profit=Decimal(total_received or 0) - total_loaned,
        client_count=clients_query.count(),
        active_loan_count=active,
        overdue_count=overdue_count,
        monthly=monthly,
    )


@router.get("/logs", response_model=list[AuditLogOut])
def logs(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(300).all()


@router.get("/notifications", response_model=list[NotificationOut])
def notifications(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Notification).order_by(Notification.created_at.desc()).limit(200).all()


@router.post("/notifications/{notification_id}/read")
def mark_read(notification_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    notification = db.get(Notification, notification_id)
    if notification:
        notification.status = "read"
        db.commit()
    return {"ok": True}
