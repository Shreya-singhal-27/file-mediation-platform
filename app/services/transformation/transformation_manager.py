from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from app.models.mapping_rule import MappingRule
from app.schemas.transformation import (
	OutputSchema,
	TransformationFieldMapping,
	TransformationResult,
	TransformationStatistics,
)
from app.services.transformation.transformation_engine import TransformationEngine
from app.utils.coercion import coerce_value



class TransformationManager:
	"""Normalizes configurable transformation inputs and delegates execution to the engine."""

	def __init__(self, transformation_engine: TransformationEngine | None = None) -> None:
		self._transformation_engine = transformation_engine or TransformationEngine()

	def transform_records(
		self,
		records: list[dict[str, Any]],
		mappings: Sequence[MappingRule | TransformationFieldMapping | dict[str, Any]],
		output_schema: OutputSchema | dict[str, Any] | None = None,
	) -> TransformationResult:
		"""Transform records using configurable mapping definitions and optional output schema."""

		if not mappings:
			return TransformationResult(
				transformed_records=[dict(record) for record in records],
				rejected_records=[],
				statistics=TransformationStatistics(
					total_records=len(records),
					transformed_records=len(records),
					rejected_records=0,
				),
			)

		normalized_mappings = self._normalize_mappings(mappings)
		normalized_schema = self._normalize_output_schema(output_schema)

		return self._transformation_engine.transform(
			records,
			normalized_mappings,
			normalized_schema,
		)

	def _normalize_mappings(
		self,
		mappings: Sequence[MappingRule | TransformationFieldMapping | dict[str, Any]],
	) -> list[TransformationFieldMapping]:
		"""Convert supported mapping inputs into engine-ready field mappings."""
		normalized_mappings: list[TransformationFieldMapping] = []

		for index, mapping in enumerate(mappings, start=1):
			if isinstance(mapping, TransformationFieldMapping):
				normalized_mappings.append(mapping)
				continue

			if isinstance(mapping, MappingRule):
				normalized_mappings.append(self._from_orm_mapping(mapping, index))
				continue

			normalized_mappings.append(self._from_mapping(mapping, index))

		return normalized_mappings

	@staticmethod
	def _normalize_output_schema(output_schema: OutputSchema | dict[str, Any] | None) -> OutputSchema | None:
		"""Normalize the optional output schema input into a Pydantic model."""
		if output_schema is None:
			return None
		if isinstance(output_schema, OutputSchema):
			return output_schema
		return OutputSchema.model_validate(output_schema)

	def _from_orm_mapping(self, mapping: MappingRule, priority: int) -> TransformationFieldMapping:
		"""Convert a SQLAlchemy mapping rule into an engine definition."""
		return TransformationFieldMapping(
			rule_id=str(mapping.id),
			source_field=mapping.source_field,
			target_field=mapping.target_field,
			transformation_type=str(mapping.transformation_type).upper(),
			parameters={},
			default_value=coerce_value(mapping.default_value),
			required=mapping.is_required,
		)

	def _from_mapping(
		self,
		mapping: dict[str, Any],
		priority: int,
	) -> TransformationFieldMapping:
		"""Convert a mapping payload into an engine definition."""
		rule_id = str(mapping.get("rule_id") or mapping.get("id") or priority)
		source_field = mapping.get("source_field")
		target_field = mapping.get("target_field")
		transformation_type = mapping.get("transformation_type")

		if source_field is None or target_field is None or transformation_type is None:
			raise ValueError(
				"Transformation mappings must define 'source_field', 'target_field' and 'transformation_type'."
			)

		parameters = mapping.get("parameters") or {}
		if not isinstance(parameters, dict):
			raise ValueError("Transformation mapping 'parameters' must be a dictionary when provided.")

		return TransformationFieldMapping(
			rule_id=rule_id,
			source_field=str(source_field),
			target_field=str(target_field),
			transformation_type=str(transformation_type).upper(),
			parameters=parameters,
			default_value=coerce_value(mapping.get("default_value")),
			required=bool(mapping.get("required", False)),
		)
