from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.schemas.transformation import OutputDataType, OutputSchema, TransformationFieldMapping, TransformationIssue


class TransformationValidator:
	"""Validates required fields and the final output schema for transformed records."""

	def validate_required_fields(
		self,
		record: dict[str, Any],
		mappings: list[TransformationFieldMapping],
	) -> list[TransformationIssue]:
		"""Validate required mapping targets before schema validation runs."""
		issues: list[TransformationIssue] = []

		for mapping in mappings:
			if not mapping.required:
				continue
			value = record.get(mapping.target_field)
			if value is None:
				issues.append(
					TransformationIssue(
						field_name=mapping.target_field,
						issue=f"Required field '{mapping.target_field}' is missing.",
						code="REQUIRED_FIELD_MISSING",
					)
				)

		return issues

	def validate_output_schema(
		self,
		record: dict[str, Any],
		output_schema: OutputSchema | None,
	) -> list[TransformationIssue]:
		"""Validate a transformed record against the configured output schema."""
		if output_schema is None:
			return []

		issues: list[TransformationIssue] = []
		for field_schema in output_schema.fields:
			value = record.get(field_schema.field_name)
			if value is None:
				if field_schema.required:
					issues.append(
						TransformationIssue(
							field_name=field_schema.field_name,
							issue=f"Required output field '{field_schema.field_name}' is missing.",
							code="OUTPUT_FIELD_MISSING",
						)
					)
				continue

			if not self._matches_type(value, field_schema.data_type):
				issues.append(
					TransformationIssue(
						field_name=field_schema.field_name,
						issue=(
							f"Field '{field_schema.field_name}' does not match expected type "
							f"'{field_schema.data_type}'."
						),
						code="OUTPUT_TYPE_MISMATCH",
					)
				)

		return issues

	@staticmethod
	def _matches_type(value: Any, data_type: OutputDataType) -> bool:
		"""Check whether a transformed value matches the configured output type."""
		if data_type == "STRING":
			return isinstance(value, str)
		if data_type == "INTEGER":
			return isinstance(value, int) and not isinstance(value, bool)
		if data_type == "FLOAT":
			return isinstance(value, float)
		if data_type == "DECIMAL":
			return isinstance(value, Decimal)
		if data_type == "BOOLEAN":
			return isinstance(value, bool)
		if data_type == "DATE":
			return isinstance(value, date) and not isinstance(value, datetime)
		if data_type == "DATETIME":
			return isinstance(value, datetime)
		if data_type == "JSON":
			return isinstance(value, (dict, list, str, int, float, bool))
		return False
