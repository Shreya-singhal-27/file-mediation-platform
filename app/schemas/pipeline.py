from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PipelineBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    source_id: int
    destination_id: int

    schedule: str | None = None

    decoder_type: str = Field(default="CSV", max_length=50)

    output_format: str = Field(default="CSV", max_length=20)

    archive_enabled: bool = True

    retry_count: int = Field(default=3, ge=0)


class PipelineCreate(PipelineBase):
    pass


class PipelineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    source_id: int | None = None
    destination_id: int | None = None

    schedule: str | None = None

    decoder_type: str | None = None

    output_format: str | None = None

    archive_enabled: bool | None = None

    retry_count: int | None = Field(default=None, ge=0)

    is_active: bool | None = None


class PipelineResponse(PipelineBase):
    id: int
    created_by_id: int

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)