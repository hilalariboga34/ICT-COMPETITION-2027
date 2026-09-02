from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


class SessionStatus(str, enum.Enum):
    """app.schemas.session.SessionStatus ile birebir aynı değerler."""

    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"


class ParticipantStatus(str, enum.Enum):
    """app.schemas.analysis.ParticipantStatus ile birebir aynı değerler."""

    ANALYZING = "analyzing"
    AUTHENTIC = "authentic"
    SUSPICIOUS = "suspicious"
    DISCONNECTED = "disconnected"


# Aynı Enum nesnesi birden fazla tabloda (participants + analysis_results)
# kullanılıyor. Aynı Python nesnesini paylaşmak, Postgres native ENUM
# tipinin (participant_status) yalnızca BİR KEZ CREATE TYPE ile
# oluşturulmasını garanti eder.
# values_callable: Postgres ENUM'un içine Python enum üyesinin .name'i
# (WAITING) değil .value'su (waiting) yazılsın — API'deki (Pydantic) string
# değerlerle birebir aynı olması için şart.
session_status_enum = SAEnum(
    SessionStatus,
    name="session_status",
    native_enum=True,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)
participant_status_enum = SAEnum(
    ParticipantStatus,
    name="participant_status",
    native_enum=True,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)
