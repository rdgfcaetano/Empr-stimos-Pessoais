from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.deps import ensure_owner_or_admin, get_current_user
from app.db.session import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.services.audit import log_action, notify_admins

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Client)
    if current_user.role != "admin":
        query = query.filter(Client.partner_id == current_user.id)
    return query.order_by(Client.created_at.desc()).all()


@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = Client(partner_id=current_user.id, **payload.model_dump())
    db.add(client)
    db.flush()
    log_action(db, user=current_user, action="create", entity="client", entity_id=client.id, new_value=payload.model_dump(), ip_address=request.client.host if request.client else None)
    notify_admins(db, actor=current_user, title="Cliente cadastrado", message=f"{current_user.name} cadastrou {client.name}.")
    db.commit()
    db.refresh(client)
    return client


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    ensure_owner_or_admin(client.partner_id, current_user)
    old = ClientOut.model_validate(client).model_dump()
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    log_action(db, user=current_user, action="update", entity="client", entity_id=client.id, old_value=old, new_value=payload.model_dump(exclude_unset=True))
    notify_admins(db, actor=current_user, title="Cliente alterado", message=f"{current_user.name} alterou {client.name}.")
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(client_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Cliente não encontrado")
    ensure_owner_or_admin(client.partner_id, current_user)
    old = ClientOut.model_validate(client).model_dump()
    db.delete(client)
    log_action(db, user=current_user, action="delete", entity="client", entity_id=client_id, old_value=old)
    notify_admins(db, actor=current_user, title="Cliente excluído", message=f"{current_user.name} excluiu {client.name}.")
    db.commit()
    return {"ok": True}
