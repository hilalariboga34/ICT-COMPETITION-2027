from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as DBSession

from app.models.model_version import ModelVersion


class ModelVersionRepository:
    def __init__(self, db_session: DBSession) -> None:
        self.db_session = db_session

    def get_or_create(self, name: str) -> ModelVersion:
        statement = (
            insert(ModelVersion)
            .values(name=name)
            .on_conflict_do_nothing(index_elements=[ModelVersion.name])
            .returning(ModelVersion)
        )
        model_version = self.db_session.execute(statement).scalar_one_or_none()
        if model_version is not None:
            return model_version

        existing_statement = select(ModelVersion).where(ModelVersion.name == name)
        return self.db_session.execute(existing_statement).scalar_one()
