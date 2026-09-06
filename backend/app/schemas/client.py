from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=140)
    phone: str = Field(min_length=3, max_length=40)
    address: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=140)
    phone: str | None = Field(default=None, min_length=3, max_length=40)
    address: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class ClientOut(ORMModel):
    id: int
    partner_id: int
    name: str
    phone: str
    address: str | None
    notes: str | None
    created_at: datetime
