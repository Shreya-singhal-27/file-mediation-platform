import json
from typing import Any


def coerce_value(value: Any) -> Any:
	"""Normalize configured values into types suitable for comparisons and transformation."""
	if value is None or isinstance(value, (int, float, bool, list, dict, tuple, set)):
		return value

	if isinstance(value, str):
		stripped_value = value.strip()
		if stripped_value.lower() == "null":
			return None

		try:
			return json.loads(stripped_value)
		except json.JSONDecodeError:
			if "," in stripped_value:
				return [part.strip() for part in stripped_value.split(",") if part.strip()]
			return stripped_value

	return value
