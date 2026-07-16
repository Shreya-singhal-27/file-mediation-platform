from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ComparisonOperator = Literal[
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "IN",
    "NOT IN",
    "LIKE",
    "NOT LIKE",
    "STARTS_WITH",
    "ENDS_WITH",
    "CONTAINS",
    "IS NULL",
    "IS NOT NULL",
]

LogicalOperator = Literal["AND", "OR"]


class FilterCondition(BaseModel):
    """Represents a single field-level filtering condition."""

    rule_id: str | None = Field(default=None, max_length=100)
    field_name: str = Field(min_length=1, max_length=100)
    operator: ComparisonOperator
    value: Any | None = None

    model_config = ConfigDict(extra="forbid")


class FilterGroup(BaseModel):
    """Represents a group of filtering conditions joined by a logical operator."""

    logical_operator: LogicalOperator = "AND"
    conditions: list[FilterCondition | FilterGroup] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class RejectedRecord(BaseModel):
    """Represents a record rejected by the filtering engine."""

    original_record: dict[str, Any]
    reject_reason: str = Field(min_length=1, max_length=500)
    rule_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime

    model_config = ConfigDict(extra="forbid")


class FilterStatistics(BaseModel):
    """Captures the outcome summary for a filtering execution."""

    total_records: int = Field(ge=0)
    accepted_records: int = Field(ge=0)
    rejected_records: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


class FilterResult(BaseModel):
    """Represents the full result of a filtering run."""

    accepted_records: list[dict[str, Any]] = Field(default_factory=list)
    rejected_records: list[RejectedRecord] = Field(default_factory=list)
    statistics: FilterStatistics

    model_config = ConfigDict(extra="forbid")