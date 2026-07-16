from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.schemas.transformation import (
	OutputSchema,
	RejectedTransformationRecord,
	TransformationFieldMapping,
	TransformationIssue,
	TransformationResult,
	TransformationStatistics,
)
from app.services.transformation.default_values import DefaultValueResolver
from app.services.transformation.field_mapper import FieldMapper
from app.services.transformation.formatters import FormatterRegistry, DEFAULT_FORMATTER_REGISTRY
from app.services.transformation.type_converter import TypeConverterRegistry, DEFAULT_TYPE_CONVERTER_REGISTRY
from app.services.transformation.validators import TransformationValidator


class BaseTransformer(ABC):
	"""Defines the shared contract and helpers for transformation components."""

	def __init__(
		self,
		field_mapper: FieldMapper | None = None,
		type_converter_registry: TypeConverterRegistry | None = None,
		formatter_registry: FormatterRegistry | None = None,
		default_value_resolver: DefaultValueResolver | None = None,
		validator: TransformationValidator | None = None,
	) -> None:
		self._field_mapper = field_mapper or FieldMapper()
		self._type_converter_registry = type_converter_registry or DEFAULT_TYPE_CONVERTER_REGISTRY
		self._formatter_registry = formatter_registry or DEFAULT_FORMATTER_REGISTRY
		self._default_value_resolver = default_value_resolver or DefaultValueResolver()
		self._validator = validator or TransformationValidator()

	@abstractmethod
	def transform(
		self,
		records: list[dict[str, Any]],
		mappings: list[TransformationFieldMapping],
		output_schema: OutputSchema | None = None,
	) -> TransformationResult:
		"""Transform a batch of records into the configured output structure."""

	@staticmethod
	def _build_rejected_record(
		original_record: dict[str, Any],
		reason: str,
		rule_id: str,
		issues: list[TransformationIssue] | None = None,
	) -> RejectedTransformationRecord:
		"""Create a normalized rejected-record payload for transformation failures."""
		return RejectedTransformationRecord(
			original_record=deepcopy(original_record),
			reject_reason=reason,
			rule_id=rule_id,
			timestamp=datetime.now(timezone.utc),
			issues=issues or [],
		)

	@staticmethod
	def _build_result(
		transformed_records: list[dict[str, Any]],
		rejected_records: list[RejectedTransformationRecord],
	) -> TransformationResult:
		"""Build a normalized transformation result with summary statistics."""
		statistics = TransformationStatistics(
			total_records=len(transformed_records) + len(rejected_records),
			transformed_records=len(transformed_records),
			rejected_records=len(rejected_records),
		)
		return TransformationResult(
			transformed_records=transformed_records,
			rejected_records=rejected_records,
			statistics=statistics,
		)
