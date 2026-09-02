"""Tüm SQLAlchemy modellerini burada import etmek, Alembic autogenerate'in
(ve Base.metadata.create_all'ın) tüm tabloları görmesini sağlar."""

from app.models.base import Base
from app.models.manipulation_method import ManipulationMethod
from app.models.dataset_video import DatasetVideo
from app.models.face_sample import FaceSample
from app.models.session import Session
from app.models.participant import Participant
from app.models.model_version import ModelVersion
from app.models.analysis_result import AnalysisResult
from app.models.session_event import SessionEvent

__all__ = [
    "Base",
    "ManipulationMethod",
    "DatasetVideo",
    "FaceSample",
    "Session",
    "Participant",
    "ModelVersion",
    "AnalysisResult",
    "SessionEvent",
]
