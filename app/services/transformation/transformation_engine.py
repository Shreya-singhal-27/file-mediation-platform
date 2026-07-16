from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Callable

from app.schemas.transformation import (
	OutputSchema,
	RejectedTransformationRecord,
	TransformationFieldMapping,
	TransformationIssue,
	TransformationResult,
)
from app.services.transformation.base_transformer import BaseTransformer
from app.services.transformation.exceptions import ConversionException, MissingSourceFieldException


@dataclass(frozen=True, slots=True)
class RecordTransformationOutcome:
	"""Represents the outcome of transforming a single source record."""

	transformed_record: dict[str, Any] | None
	issues: list[TransformationIssue]
	rule_id: str | None = None


class TransformationEngine(BaseTransformer):
	"""Transforms decoded records into the configured output structure."""

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		self._handlers: dict[str, Callable[[Any, TransformationFieldMapping], Any]] = {
			"COPY": self._handle_copy,
			"DEFAULT_VALUE": self._handle_default_value,
			"BOOLEAN_CONVERSION": self._handle_boolean_conversion,
			"DATE_FORMAT": self._handle_date_format,
			"NUMBER_FORMAT": self._handle_number_format,
		}

	def transform(
		self,
		records: list[dict[str, Any]],
		mappings: list[TransformationFieldMapping],
		output_schema: OutputSchema | None = None,
	) -> TransformationResult:
		"""Transform a batch of records using the configured mapping definitions."""
		transformed_records: list[dict[str, Any]] = []
		rejected_records: list[RejectedTransformationRecord] = []

		for record in records:
			outcome = self._transform_record(record, mappings, output_schema)
			if outcome.transformed_record is None:
				rejected_records.append(
					self._build_rejected_record(
						original_record=record,
						reason=outcome.issues[0].issue,
						rule_id=outcome.rule_id or "transformation",
						issues=outcome.issues,
					)
				)
				continue

			transformed_records.append(outcome.transformed_record)

		return self._build_result(transformed_records, rejected_records)

	def _transform_record(
		self,
		record: dict[str, Any],
		mappings: list[TransformationFieldMapping],
		output_schema: OutputSchema | None,
	) -> RecordTransformationOutcome:
		"""Transform a single decoded record using the configured mappings."""
		mapped_record = self._field_mapper.map_record(record, mappings)
		transformed_record = deepcopy(mapped_record)
		issues: list[TransformationIssue] = []
		current_rule_id: str | None = None

		for mapping in mappings:
			current_rule_id = mapping.rule_id or mapping.source_field
			raw_value = mapped_record.get(mapping.target_field)

			try:
				transformed_value = self._apply_transformation(raw_value, mapping)
			except (ConversionException, MissingSourceFieldException) as exc:
				issues.append(
					TransformationIssue(
						field_name=mapping.target_field,
						issue=str(exc),
						code="TRANSFORMATION_FAILED",
					)
				)
				return RecordTransformationOutcome(
					transformed_record=None,
					issues=issues,
					rule_id=current_rule_id,
				)

			transformed_record[mapping.target_field] = transformed_value

			if mapping.required and transformed_record.get(mapping.target_field) is None:
				issues.append(
					TransformationIssue(
						field_name=mapping.target_field,
						issue=f"Required field '{mapping.target_field}' is missing after transformation.",
						code="REQUIRED_FIELD_MISSING",
					)
				)

		required_field_issues = self._validator.validate_required_fields(transformed_record, mappings)
		issues.extend(required_field_issues)
		issues.extend(self._validator.validate_output_schema(transformed_record, output_schema))

		if issues:
			return RecordTransformationOutcome(
				transformed_record=None,
				issues=issues,
				rule_id=current_rule_id,
			)

		return RecordTransformationOutcome(
			transformed_record=transformed_record,
			issues=[],
			rule_id=current_rule_id,
		)

	def _apply_transformation(
		self,
		value: Any,
		mapping: TransformationFieldMapping,
	) -> Any:
		"""Apply the configured transformation type to a single mapped field."""
		transformation_handler = self._handlers.get(mapping.transformation_type)
		if transformation_handler is None:
			raise ConversionException(
				f"Unsupported transformation type '{mapping.transformation_type}'."
			)

		value = self._default_value_resolver.resolve(value, mapping.default_value)
		return transformation_handler(value, mapping)

	def _handle_copy(self, value: Any, mapping: TransformationFieldMapping) -> Any:
		"""Return the mapped value unchanged."""
		return value

	def _handle_default_value(self, value: Any, mapping: TransformationFieldMapping) -> Any:
		"""Use the configured default when the source value is empty."""
		return self._default_value_resolver.resolve(value, mapping.default_value)

	def _handle_boolean_conversion(self, value: Any, mapping: TransformationFieldMapping) -> bool | None:
		"""Convert the mapped value to a boolean."""
		return self._type_converter_registry.get("BOOLEAN").convert(value)

	def _handle_date_format(self, value: Any, mapping: TransformationFieldMapping) -> str | None:
		"""Convert and format the mapped value as a date string."""
		converted_value = self._type_converter_registry.get("DATETIME").convert(value, mapping.parameters.get("input_format"))
		pattern = mapping.parameters.get("format") or mapping.parameters.get("output_format")
		if isinstance(converted_value, datetime):
			return self._formatter_registry.get("DATE_FORMAT").format(converted_value, pattern)
		if isinstance(converted_value, date):
			return self._formatter_registry.get("DATE_FORMAT").format(converted_value, pattern)
		raise ConversionException(f"Unable to format value '{value}' as a date.")

	def _handle_number_format(self, value: Any, mapping: TransformationFieldMapping) -> str | None:
		"""Convert and format the mapped value as a numeric string."""
		converted_value = self._type_converter_registry.get("DECIMAL").convert(value)
		pattern = mapping.parameters.get("format") or mapping.parameters.get("output_format")
		return self._formatter_registry.get("NUMBER_FORMAT").format(converted_value, pattern)
