from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    source_ip: Mapped[str] = mapped_column(String(64), default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
