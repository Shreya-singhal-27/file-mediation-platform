from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DestinationBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    destination_type: str = Field(min_length=2, max_length=30)
    config: dict[str, Any]


class DestinationCreate(DestinationBase):
    pass


class DestinationUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    destination_type: str | None = Field(default=None, max_length=30)
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class DestinationResponse(DestinationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)