from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ParticipantStatus, participant_status_enum


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # RESTRICT: session silinmeye çalışılırsa (olmamalı ama), içinde
        # participant kaydı varsa Postgres bunu reddeder. Cascade YOK.
        ForeignKey("sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ParticipantStatus] = mapped_column(
        participant_status_enum,
        nullable=False,
        server_default=ParticipantStatus.ANALYZING.value,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Katılımcı ayrıldığında kayıt SİLİNMEZ; left_at doldurulur ve
    # status='disconnected' olarak güncellenir.
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    session: Mapped["Session"] = relationship(back_populates="participants")
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="participant"
    )
