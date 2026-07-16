from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, ClassVar

from app.schemas.transformation import OutputDataType
from app.services.transformation.exceptions import ConversionException, UnsupportedTransformationTypeException


class BaseTypeConverter(ABC):
	"""Defines the contract for a single output data type converter."""

	output_type: ClassVar[OutputDataType]

	@abstractmethod
	def convert(self, value: Any, format: str | None = None) -> Any:
		"""Convert a value into the target Python representation."""


class StringConverter(BaseTypeConverter):
	"""Converts values to string."""

	output_type = "STRING"

	def convert(self, value: Any, format: str | None = None) -> str | None:
		if value is None:
			return None
		return str(value)


class IntegerConverter(BaseTypeConverter):
	"""Converts values to integer."""

	output_type = "INTEGER"

	def convert(self, value: Any, format: str | None = None) -> int | None:
		if value is None:
			return None
		try:
			return int(value)
		except (TypeError, ValueError) as exc:
			raise ConversionException(f"Unable to convert value '{value}' to integer.") from exc


class FloatConverter(BaseTypeConverter):
	"""Converts values to float."""

	output_type = "FLOAT"

	def convert(self, value: Any, format: str | None = None) -> float | None:
		if value is None:
			return None
		try:
			return float(value)
		except (TypeError, ValueError) as exc:
			raise ConversionException(f"Unable to convert value '{value}' to float.") from exc


class DecimalConverter(BaseTypeConverter):
	"""Converts values to Decimal."""

	output_type = "DECIMAL"

	def convert(self, value: Any, format: str | None = None) -> Decimal | None:
		if value is None:
			return None
		try:
			return Decimal(str(value))
		except (InvalidOperation, TypeError, ValueError) as exc:
			raise ConversionException(f"Unable to convert value '{value}' to decimal.") from exc


class BooleanConverter(BaseTypeConverter):
	"""Converts values to boolean."""

	output_type = "BOOLEAN"

	TRUE_VALUES = {"true", "1", "yes", "y", "on", True, 1}
	FALSE_VALUES = {"false", "0", "no", "n", "off", False, 0}

	def convert(self, value: Any, format: str | None = None) -> bool | None:
		if value is None:
			return None
		if value in self.TRUE_VALUES:
			return True
		if value in self.FALSE_VALUES:
			return False
		if isinstance(value, str):
			normalized = value.strip().lower()
			if normalized in {"true", "1", "yes", "y", "on"}:
				return True
			if normalized in {"false", "0", "no", "n", "off"}:
				return False
		raise ConversionException(f"Unable to convert value '{value}' to boolean.")


class DateConverter(BaseTypeConverter):
	"""Converts values to date instances."""

	output_type = "DATE"

	def convert(self, value: Any, format: str | None = None) -> date | None:
		if value is None:
			return None
		if isinstance(value, date) and not isinstance(value, datetime):
			return value
		parsed_datetime = _parse_datetime(value, format)
		return parsed_datetime.date()


class DateTimeConverter(BaseTypeConverter):
	"""Converts values to datetime instances."""

	output_type = "DATETIME"

	def convert(self, value: Any, format: str | None = None) -> datetime | None:
		if value is None:
			return None
		if isinstance(value, datetime):
			return value
		return _parse_datetime(value, format)


class JsonConverter(BaseTypeConverter):
	"""Leaves structured values intact and parses JSON strings when needed."""

	output_type = "JSON"

	def convert(self, value: Any, format: str | None = None) -> Any:
		if value is None:
			return None
		if isinstance(value, (dict, list, int, float, bool)):
			return value
		if isinstance(value, str):
			import json

			try:
				return json.loads(value)
			except json.JSONDecodeError as exc:
				raise ConversionException(f"Unable to parse JSON value '{value}'.") from exc
		raise ConversionException(f"Unable to convert value '{value}' to JSON.")


class TypeConverterRegistry:
	"""Resolves type converters by output data type."""

	def __init__(self) -> None:
		self._converters: dict[str, BaseTypeConverter] = {}

	def register(self, converter: BaseTypeConverter) -> None:
		"""Register a concrete converter implementation."""
		self._converters[converter.output_type] = converter

	def get(self, output_type: OutputDataType) -> BaseTypeConverter:
		"""Return the matching converter for an output type."""
		converter = self._converters.get(output_type)
		if converter is None:
			raise UnsupportedTransformationTypeException(
				f"Unsupported transformation type '{output_type}'."
			)
		return converter

	def available(self) -> list[str]:
		"""Return the registered output types."""
		return sorted(self._converters.keys())


def build_default_type_converter_registry() -> TypeConverterRegistry:
	"""Create the registry containing all built-in type converters."""
	registry = TypeConverterRegistry()
	registry.register(StringConverter())
	registry.register(IntegerConverter())
	registry.register(FloatConverter())
	registry.register(DecimalConverter())
	registry.register(BooleanConverter())
	registry.register(DateConverter())
	registry.register(DateTimeConverter())
	registry.register(JsonConverter())
	return registry


DEFAULT_TYPE_CONVERTER_REGISTRY = build_default_type_converter_registry()


def _parse_datetime(value: Any, format: str | None = None) -> datetime:
	"""Parse a datetime using an optional explicit format or common fallbacks."""
	if isinstance(value, datetime):
		return value
	if isinstance(value, date):
		return datetime.combine(value, datetime.min.time())
	if not isinstance(value, str):
		raise ConversionException(f"Unable to convert value '{value}' to datetime.")

	patterns = [format] if format else []
	patterns.extend([
		"%Y-%m-%dT%H:%M:%S.%f",
		"%Y-%m-%dT%H:%M:%S",
		"%Y-%m-%d %H:%M:%S",
		"%Y-%m-%d",
	])

	last_error: Exception | None = None
	for pattern in patterns:
		if pattern is None:
			continue
		try:
			return datetime.strptime(value, pattern)
		except ValueError as exc:
			last_error = exc

	try:
		return datetime.fromisoformat(value)
	except ValueError as exc:
		last_error = exc

	raise ConversionException(f"Unable to convert value '{value}' to datetime.") from last_error
