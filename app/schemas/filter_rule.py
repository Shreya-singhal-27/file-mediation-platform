from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FilterRuleBase(BaseModel):
    rule_name: str = Field(min_length=2, max_length=100)

    field_name: str = Field(min_length=1, max_length=100)

    operator: str = Field(max_length=20)

    value: str

    logical_operator: str | None = None

    priority: int = Field(default=1, ge=1)


class FilterRuleCreate(FilterRuleBase):
    pipeline_id: int


class FilterRuleUpdate(BaseModel):
    rule_name: str | None = None

    field_name: str | None = None

    operator: str | None = None

    value: str | None = None

    logical_operator: str | None = None

    priority: int | None = Field(default=None, ge=1)

    is_active: bool | None = None


class FilterRuleResponse(FilterRuleBase):
    id: int

    pipeline_id: int

    is_active: bool

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)