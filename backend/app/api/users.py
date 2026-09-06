from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.name).all()


@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.flush()
    log_action(db, user=admin, action="create", entity="user", entity_id=user.id, new_value=payload.model_dump(), ip_address=request.client.host if request.client else None)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    old = {"name": user.name, "email": user.email, "role": user.role, "is_active": user.is_active}
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "password":
            user.password_hash = hash_password(value)
            log_action(db, user=admin, action="password_reset", entity="user", entity_id=user.id)
        else:
            setattr(user, key, value)
    log_action(db, user=admin, action="update", entity="user", entity_id=user.id, old_value=old, new_value=payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(user)
    return user
