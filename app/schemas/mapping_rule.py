from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MappingRuleBase(BaseModel):
    source_field: str = Field(min_length=1, max_length=100)

    target_field: str = Field(min_length=1, max_length=100)

    transformation_type: str = Field(max_length=50)

    default_value: str | None = None

    is_required: bool = False


class MappingRuleCreate(MappingRuleBase):
    pipeline_id: int


class MappingRuleUpdate(BaseModel):
    source_field: str | None = None

    target_field: str | None = None

    transformation_type: str | None = None

    default_value: str | None = None

    is_required: bool | None = None


class MappingRuleResponse(MappingRuleBase):
    id: int

    pipeline_id: int

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)