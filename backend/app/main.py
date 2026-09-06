from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, clients, loans, users
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import *  # noqa: F401,F403
from app.models.enums import UserRole
from app.models.user import User

settings = get_settings()
app = FastAPI(title="Sistema de Gestão de Empréstimos", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == "admin@local").first()
        if not exists:
            db.add(
                User(
                    name="Administrador",
                    email="admin@local",
                    password_hash=hash_password("Admin123!"),
                    role=UserRole.ADMIN,
                )
            )
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(loans.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
