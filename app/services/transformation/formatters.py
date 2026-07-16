from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Any, ClassVar

from app.services.transformation.exceptions import ConversionException, UnsupportedTransformationTypeException


class BaseFormatter(ABC):
	"""Defines the contract for a single formatting strategy."""

	format_name: ClassVar[str]

	@abstractmethod
	def format(self, value: Any, pattern: str | None = None) -> Any:
		"""Format a value into the target representation."""


class DateFormatter(BaseFormatter):
	"""Formats date and datetime values using a strftime pattern."""

	format_name = "DATE_FORMAT"

	def format(self, value: Any, pattern: str | None = None) -> str | None:
		if value is None:
			return None
		if not isinstance(value, (date, datetime)):
			raise ConversionException(f"Unable to format non-date value '{value}' as date.")

		strftime_pattern = pattern or "%Y-%m-%d"
		return value.strftime(strftime_pattern)


class NumberFormatter(BaseFormatter):
	"""Formats numeric values using a Python format specification."""

	format_name = "NUMBER_FORMAT"

	def format(self, value: Any, pattern: str | None = None) -> str | None:
		if value is None:
			return None
		if not isinstance(value, (int, float, Decimal)):
			raise ConversionException(f"Unable to format non-numeric value '{value}' as number.")

		if pattern is None:
			return str(value)

		return format(value, pattern)


class PassthroughFormatter(BaseFormatter):
	"""Leaves values unchanged when no explicit formatting is required."""

	format_name = "COPY"

	def format(self, value: Any, pattern: str | None = None) -> Any:
		return value


class FormatterRegistry:
	"""Resolves formatting strategies by transformation type."""

	def __init__(self) -> None:
		self._formatters: dict[str, BaseFormatter] = {}

	def register(self, formatter: BaseFormatter) -> None:
		"""Register a formatter implementation."""
		self._formatters[formatter.format_name] = formatter

	def get(self, format_name: str) -> BaseFormatter:
		"""Return the registered formatter or fail fast if unsupported."""
		formatter = self._formatters.get(format_name)
		if formatter is None:
			raise UnsupportedTransformationTypeException(
				f"Unsupported formatting type '{format_name}'."
			)
		return formatter

	def available(self) -> list[str]:
		"""Return supported formatter names."""
		return sorted(self._formatters.keys())


def build_default_formatter_registry() -> FormatterRegistry:
	"""Create the default registry with built-in formatters registered."""
	registry = FormatterRegistry()
	registry.register(DateFormatter())
	registry.register(NumberFormatter())
	registry.register(PassthroughFormatter())
	return registry


DEFAULT_FORMATTER_REGISTRY = build_default_formatter_registry()
