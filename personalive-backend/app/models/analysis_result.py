from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ParticipantStatus, participant_status_enum


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    __table_args__ = (
        CheckConstraint(
            "reality_score >= 0.0 AND reality_score <= 1.0",
            name="ck_analysis_results_reality_score_range",
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_analysis_results_confidence_range",
        ),
        # Sadece "participant_id gerçekten var mı" değil, "bu participant
        # gerçekten BU session'a mı ait" diye composite FK ile doğruluyoruz.
        # participants.(id, session_id) üzerindeki UNIQUE constraint'e
        # (bkz. app/models/participant.py) referans veriyor. Session A'ya,
        # Session B'deki bir participant ile analiz kaydı eklenemez.
        ForeignKeyConstraint(
            ["participant_id", "session_id"],
            ["participants.id", "participants.session_id"],
            ondelete="RESTRICT",
            name="fk_analysis_results_participant_session",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # participant_id'nin kendi başına ayrı bir ForeignKey'i YOK — yukarıdaki
    # composite ForeignKeyConstraint zaten (participant_id, session_id)
    # çiftinin participants'ta var olmasını (ve doğru session'a ait
    # olmasını) garanti ediyor, bu da tek başına participant_id'nin geçerli
    # olmasını da kapsıyor.
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    model_version_id: Mapped[int] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reality_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[ParticipantStatus] = mapped_column(
        participant_status_enum, nullable=False
    )
    # AnalysisInput/AnalysisResult şemasındaki analiz zamanı — indexli
    # (Hilal'in "timestamp" için index isteği).
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # overlaps: composite FK (participant_id, session_id) yüzünden bu iki
    # ilişki de session_id kolonunu "paylaşıyor" — kasıtlı, bkz.
    # app/models/participant.py'deki aynı isimli not.
    session: Mapped["Session"] = relationship(
        back_populates="analysis_results", overlaps="analysis_results"
    )
    participant: Mapped["Participant"] = relationship(
        back_populates="analysis_results", overlaps="analysis_results,session"
    )
    model_version: Mapped["ModelVersion"] = relationship(
        back_populates="analysis_results"
    )
