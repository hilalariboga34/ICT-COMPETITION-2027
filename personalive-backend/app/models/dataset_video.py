from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DatasetVideo(Base):
    __tablename__ = "dataset_videos"
    __table_args__ = (
        CheckConstraint(
            "label IS NULL OR label IN (0, 1)",
            name="ck_dataset_videos_label_binary",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_video_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    method_id: Mapped[int] = mapped_column(
        ForeignKey("manipulation_methods.id"), nullable=False
    )
    label: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    method: Mapped["ManipulationMethod"] = relationship(back_populates="videos")
    face_samples: Mapped[list["FaceSample"]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
