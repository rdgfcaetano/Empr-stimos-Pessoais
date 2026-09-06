import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog, Notification
from app.models.enums import UserRole
from app.models.user import User


def _dump(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, default=str, ensure_ascii=False)


def log_action(
    db: Session,
    *,
    user: User | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    old_value: Any = None,
    new_value: Any = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action=action,
            entity=entity,
            entity_id=entity_id,
            old_value=_dump(old_value),
            new_value=_dump(new_value),
            ip_address=ip_address,
        )
    )


def notify_admins(db: Session, *, actor: User, title: str, message: str) -> None:
    if actor.role == UserRole.ADMIN:
        return
    db.add(Notification(actor_id=actor.id, title=title, message=message))
