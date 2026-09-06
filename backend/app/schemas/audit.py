from datetime import datetime

from app.schemas.common import ORMModel


class AuditLogOut(ORMModel):
    id: int
    user_id: int | None
    action: str
    entity: str
    entity_id: int | None
    old_value: str | None
    new_value: str | None
    ip_address: str | None
    created_at: datetime


class NotificationOut(ORMModel):
    id: int
    actor_id: int | None
    title: str
    message: str
    status: str
    created_at: datetime
