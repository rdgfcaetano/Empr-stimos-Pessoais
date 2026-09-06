from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.session import UserSession
from app.models.user import User
from app.schemas.user import LoginIn, TokenOut, UserOut
from app.services.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    token, jti = create_access_token(str(user.id))
    db.add(UserSession(user_id=user.id, token_jti=jti, ip_address=request.client.host if request.client else None))
    log_action(db, user=user, action="login", entity="user", entity_id=user.id, ip_address=request.client.host if request.client else None)
    db.commit()
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_action(db, user=current_user, action="logout", entity="user", entity_id=current_user.id)
    db.commit()
    return {"ok": True, "logged_out_at": datetime.utcnow()}
