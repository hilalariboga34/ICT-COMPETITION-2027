from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import SessionStatus, session_status_enum


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        session_status_enum, nullable=False, server_default=SessionStatus.WAITING.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Session fiziksel olarak silinmez; toplantı bittiğinde status='ended'
    # yapılır, ended_at doldurulur. Aşağıdaki iki alan bilerek nullable.
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    participants: Mapped[list["Participant"]] = relationship(back_populates="session")
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="session"
    )
    events: Mapped[list["SessionEvent"]] = relationship(back_populates="session")
