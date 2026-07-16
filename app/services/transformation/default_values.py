from __future__ import annotations

from typing import Any


class DefaultValueResolver:
	"""Resolves configured defaults without mutating the source record."""

	def resolve(self, value: Any, default_value: Any | None) -> Any:
		"""Return the existing value when present, otherwise the configured default."""
		if value is not None:
			return value
		return default_value

	def resolve_for_field(
		self,
		record: dict[str, Any],
		field_name: str,
		default_value: Any | None = None,
	) -> Any:
		"""Resolve a value from a record and fall back to the provided default."""
		value = self._resolve_nested_value(record, field_name)
		return self.resolve(value, default_value)

	@staticmethod
	def _resolve_nested_value(record: dict[str, Any], field_path: str) -> Any:
		"""Read a dotted field path from a nested source record."""
		current_value: Any = record
		for segment in field_path.split("."):
			if not isinstance(current_value, dict) or segment not in current_value:
				return None
			current_value = current_value[segment]
		return current_value
