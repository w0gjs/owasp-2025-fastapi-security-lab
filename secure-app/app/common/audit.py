from fastapi import Request
from sqlalchemy.orm import Session

from app.models.security_event import SecurityEvent


def record_security_event(
    db: Session,
    request: Request,
    event_type: str,
    description: str,
    user_id: int | None = None,
) -> None:
    source_ip = request.client.host if request.client else "unknown"
    db.add(
        SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            description=description,
            source_ip=source_ip,
        )
    )
    db.commit()
