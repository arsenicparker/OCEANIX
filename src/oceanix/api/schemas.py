"""Response schemas for the OCEANIX data-playground API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health of the local API and prepared INCOIS snapshot."""

    status: str = Field("ok", description="API process status")
    data_loaded: bool = Field(..., description="Whether the prepared INCOIS snapshot is loaded")
    snapshot_date: Optional[str] = Field(None, description="Local date on which source data was collected")
