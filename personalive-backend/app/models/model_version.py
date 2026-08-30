from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ModelVersion(Base):
    """Analiz API'sinden gelen 'modelVersion' metnine (örn. "analysis-v1")
    karşılık gelen kayıt. API bu değeri düz metin olarak gönderiyor; bu
    tablo o metni tekilleştirip analysis_results'a FK ile bağlamayı sağlar
    (manipulation_methods tablosuyla aynı desen)."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="model_version"
    )
