from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


TransformationType = Literal[
	"COPY",
	"DATE_FORMAT",
	"NUMBER_FORMAT",
	"BOOLEAN_CONVERSION",
	"DEFAULT_VALUE",
]

OutputDataType = Literal[
	"STRING",
	"INTEGER",
	"FLOAT",
	"DECIMAL",
	"BOOLEAN",
	"DATE",
	"DATETIME",
	"JSON",
]


class TransformationFieldMapping(BaseModel):
	"""Defines how a source field should be transformed into a target field."""

	rule_id: str | None = Field(default=None, max_length=100)
	source_field: str = Field(min_length=1, max_length=100)
	target_field: str = Field(min_length=1, max_length=100)
	transformation_type: TransformationType = "COPY"
	parameters: dict[str, Any] = Field(default_factory=dict)
	default_value: Any | None = None
	required: bool = False

	model_config = ConfigDict(extra="forbid")


class OutputSchemaField(BaseModel):
	"""Defines the expected target field structure after transformation."""

	field_name: str = Field(min_length=1, max_length=100)
	data_type: OutputDataType = "STRING"
	required: bool = False
	default_value: Any | None = None
	format: str | None = Field(default=None, max_length=100)

	model_config = ConfigDict(extra="forbid")


class OutputSchema(BaseModel):
	"""Represents the expected output contract for a transformed record batch."""

	fields: list[OutputSchemaField] = Field(default_factory=list)

	model_config = ConfigDict(extra="forbid")


class TransformationIssue(BaseModel):
	"""Captures a single transformation validation or conversion issue."""

	field_name: str = Field(min_length=1, max_length=100)
	issue: str = Field(min_length=1, max_length=500)
	code: str = Field(min_length=1, max_length=100)

	model_config = ConfigDict(extra="forbid")


class RejectedTransformationRecord(BaseModel):
	"""Represents a record rejected during transformation or schema validation."""

	original_record: dict[str, Any]
	reject_reason: str = Field(min_length=1, max_length=500)
	rule_id: str = Field(min_length=1, max_length=100)
	timestamp: datetime
	issues: list[TransformationIssue] = Field(default_factory=list)

	model_config = ConfigDict(extra="forbid")


class TransformationStatistics(BaseModel):
	"""Summarizes the outcome of a transformation execution."""

	total_records: int = Field(ge=0)
	transformed_records: int = Field(ge=0)
	rejected_records: int = Field(ge=0)

	model_config = ConfigDict(extra="forbid")


class TransformationResult(BaseModel):
	"""Represents the full result of a transformation run."""

	transformed_records: list[dict[str, Any]] = Field(default_factory=list)
	rejected_records: list[RejectedTransformationRecord] = Field(default_factory=list)
	statistics: TransformationStatistics

	model_config = ConfigDict(extra="forbid")