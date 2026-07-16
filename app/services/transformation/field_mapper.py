from __future__ import annotations

from typing import Any

from app.schemas.transformation import TransformationFieldMapping


class FieldMapper:
	"""Maps source record fields into their configured target field names."""

	def map_record(
		self,
		record: dict[str, Any],
		mappings: list[TransformationFieldMapping],
	) -> dict[str, Any]:
		"""Return a new record containing mapped target fields and raw values."""
		mapped_record: dict[str, Any] = {}

		for mapping in mappings:
			value = self._resolve_value(record, mapping.source_field)
			if value is None and mapping.default_value is not None:
				value = mapping.default_value

			mapped_record[mapping.target_field] = value

		return mapped_record

	@staticmethod
	def _resolve_value(record: dict[str, Any], field_path: str) -> Any:
		"""Resolve a possibly nested field path from the source record."""
		current_value: Any = record
		for segment in field_path.split("."):
			if not isinstance(current_value, dict) or segment not in current_value:
				return None
			current_value = current_value[segment]
		return current_value
