from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import AnalysisResult


class AnalysisUpdatedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["analysis.updated"] = Field(...)
    data: AnalysisResult = Field(...)
