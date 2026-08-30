from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FaceSample(Base):
    __tablename__ = "face_samples"
    __table_args__ = (
        # UNIQUE: aynı videonun aynı karesindeki aynı yüz örneği iki kez eklenemez.
        Index(
            "ix_face_samples_video_frame_face",
            "dataset_video_id",
            "frame_reference",
            "face_order",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_video_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_videos.id", ondelete="CASCADE"), nullable=False
    )
    frame_reference: Mapped[int] = mapped_column(Integer, nullable=False)
    face_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    label: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    relative_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    video: Mapped["DatasetVideo"] = relationship(back_populates="face_samples")
