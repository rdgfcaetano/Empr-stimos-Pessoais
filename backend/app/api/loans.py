from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.deps import ensure_owner_or_admin, get_current_user
from app.db.session import get_db
from app.models.client import Client
from app.models.enums import LoanStatus
from app.models.loan import Loan
from app.models.payment import Payment
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanOut, LoanUpdate
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services.audit import log_action, notify_admins
from app.services.loans import calculate_loan_totals

router = APIRouter(prefix="/loans", tags=["loans"])


def _loan_out(loan: Loan) -> LoanOut:
    data = LoanOut.model_validate(loan)
    data.totals = calculate_loan_totals(loan)
    return data


def _payment_out(payment: Payment) -> PaymentOut:
    data = PaymentOut.model_validate(payment)
    data.responsible_user_name = payment.responsible_user.name if payment.responsible_user else None
    return data


@router.get("", response_model=list[LoanOut])
def list_loans(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Loan).options(joinedload(Loan.payments))
    if current_user.role != "admin":
        query = query.filter(Loan.partner_id == current_user.id)
    return [_loan_out(loan) for loan in query.order_by(Loan.created_at.desc()).all()]


@router.post("", response_model=LoanOut)
def create_loan(payload: LoanCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    ensure_owner_or_admin(client.partner_id, current_user)
    loan = Loan(partner_id=client.partner_id, **payload.model_dump())
    db.add(loan)
    db.flush()
    log_action(db, user=current_user, action="create", entity="loan", entity_id=loan.id, new_value=payload.model_dump())
    notify_admins(db, actor=current_user, title="Empréstimo cadastrado", message=f"{current_user.name} cadastrou o empréstimo #{loan.id}.")
    db.commit()
    db.refresh(loan)
    return _loan_out(loan)


@router.delete("/{loan_id}")
def delete_loan(loan_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan = db.query(Loan).options(joinedload(Loan.payments)).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Emprestimo nao encontrado")
    ensure_owner_or_admin(loan.partner_id, current_user)
    old = LoanOut.model_validate(loan).model_dump()
    db.delete(loan)
    log_action(db, user=current_user, action="delete", entity="loan", entity_id=loan_id, old_value=old)
    notify_admins(db, actor=current_user, title="Emprestimo excluido", message=f"{current_user.name} excluiu o emprestimo #{loan_id}.")
    db.commit()
    return {"ok": True}


@router.put("/{loan_id}", response_model=LoanOut)
def update_loan(loan_id: int, payload: LoanUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan = db.query(Loan).options(joinedload(Loan.payments)).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Empréstimo não encontrado")
    ensure_owner_or_admin(loan.partner_id, current_user)
    if payload.client_id:
        client = db.get(Client, payload.client_id)
        if not client:
            raise HTTPException(404, "Cliente não encontrado")
        ensure_owner_or_admin(client.partner_id, current_user)
        loan.partner_id = client.partner_id
    old = LoanOut.model_validate(loan).model_dump()
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(loan, key, value)
    log_action(db, user=current_user, action="update", entity="loan", entity_id=loan.id, old_value=old, new_value=payload.model_dump(exclude_unset=True))
    notify_admins(db, actor=current_user, title="Empréstimo alterado", message=f"{current_user.name} alterou o empréstimo #{loan.id}.")
    db.commit()
    db.refresh(loan)
    return _loan_out(loan)


@router.post("/{loan_id}/payments", response_model=PaymentOut)
def create_payment(loan_id: int, payload: PaymentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan = db.query(Loan).options(joinedload(Loan.payments)).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Empréstimo não encontrado")
    ensure_owner_or_admin(loan.partner_id, current_user)
    payment = Payment(loan_id=loan.id, responsible_user_id=current_user.id, **payload.model_dump())
    db.add(payment)
    db.flush()
    loan.payments.append(payment)
    totals = calculate_loan_totals(loan)
    if totals["total_due"] == 0:
        loan.status = LoanStatus.PAID
    log_action(db, user=current_user, action="payment", entity="loan", entity_id=loan.id, new_value=payload.model_dump())
    notify_admins(db, actor=current_user, title="Pagamento registrado", message=f"{current_user.name} registrou pagamento no empréstimo #{loan.id}.")
    db.commit()
    db.refresh(payment)
    return _payment_out(payment)


@router.get("/{loan_id}/payments", response_model=list[PaymentOut])
def list_payments(loan_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(404, "Empréstimo não encontrado")
    ensure_owner_or_admin(loan.partner_id, current_user)
    payments = db.query(Payment).options(joinedload(Payment.responsible_user)).filter(Payment.loan_id == loan.id).order_by(Payment.paid_at.desc()).all()
    return [_payment_out(payment) for payment in payments]
