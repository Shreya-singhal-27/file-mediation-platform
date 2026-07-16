from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app.services.filtering.exceptions import UnsupportedFilterOperatorException


class BaseFilterOperator(ABC):
	"""Defines the contract for a single filter operator implementation."""

	operator_name: ClassVar[str]

	@abstractmethod
	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		"""Return True when the operator matches the supplied values."""


class EqualsOperator(BaseFilterOperator):
	"""Implements the equality operator."""

	operator_name = "="

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value == expected_value


class NotEqualsOperator(BaseFilterOperator):
	"""Implements the inequality operator."""

	operator_name = "!="

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value != expected_value


class GreaterThanOperator(BaseFilterOperator):
	"""Implements the greater-than operator."""

	operator_name = ">"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value > expected_value


class GreaterThanOrEqualOperator(BaseFilterOperator):
	"""Implements the greater-than-or-equal operator."""

	operator_name = ">="

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value >= expected_value


class LessThanOperator(BaseFilterOperator):
	"""Implements the less-than operator."""

	operator_name = "<"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value < expected_value


class LessThanOrEqualOperator(BaseFilterOperator):
	"""Implements the less-than-or-equal operator."""

	operator_name = "<="

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value <= expected_value


class InOperator(BaseFilterOperator):
	"""Implements membership checking."""

	operator_name = "IN"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value in _ensure_iterable(expected_value)


class NotInOperator(BaseFilterOperator):
	"""Implements non-membership checking."""

	operator_name = "NOT IN"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value not in _ensure_iterable(expected_value)


class LikeOperator(BaseFilterOperator):
	"""Implements SQL-like wildcard matching."""

	operator_name = "LIKE"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return _like_match(record_value, expected_value)


class NotLikeOperator(BaseFilterOperator):
	"""Implements the inverse of SQL-like wildcard matching."""

	operator_name = "NOT LIKE"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return not _like_match(record_value, expected_value)


class StartsWithOperator(BaseFilterOperator):
	"""Checks whether a value starts with the expected prefix."""

	operator_name = "STARTS_WITH"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		if record_value is None or expected_value is None:
			return False
		return str(record_value).startswith(str(expected_value))


class EndsWithOperator(BaseFilterOperator):
	"""Checks whether a value ends with the expected suffix."""

	operator_name = "ENDS_WITH"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		if record_value is None or expected_value is None:
			return False
		return str(record_value).endswith(str(expected_value))


class ContainsOperator(BaseFilterOperator):
	"""Checks whether a value contains the expected substring."""

	operator_name = "CONTAINS"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		if record_value is None or expected_value is None:
			return False
		return str(expected_value) in str(record_value)


class IsNullOperator(BaseFilterOperator):
	"""Checks whether the value is None."""

	operator_name = "IS NULL"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value is None


class IsNotNullOperator(BaseFilterOperator):
	"""Checks whether the value is not None."""

	operator_name = "IS NOT NULL"

	def evaluate(self, record_value: Any, expected_value: Any) -> bool:
		return record_value is not None


class FilterOperatorRegistry:
	"""Stores and resolves filter operator implementations by name."""

	def __init__(self) -> None:
		self._operators: dict[str, BaseFilterOperator] = {}

	def register(self, operator: BaseFilterOperator) -> None:
		"""Register an operator implementation."""
		self._operators[operator.operator_name.upper()] = operator

	def get(self, operator_name: str) -> BaseFilterOperator:
		"""Return the matching operator implementation or raise if missing."""
		operator = self._operators.get(operator_name.upper())
		if operator is None:
			raise UnsupportedFilterOperatorException(
				f"Unsupported filter operator '{operator_name}'."
			)
		return operator

	def available(self) -> list[str]:
		"""Return all supported operator names."""
		return sorted(self._operators.keys())


def _ensure_iterable(value: Any) -> list[Any]:
	"""Normalize a configured value into a list for membership checks."""
	if value is None:
		return []
	if isinstance(value, (list, tuple, set, frozenset)):
		return list(value)
	return [value]


def _like_match(record_value: Any, expected_value: Any) -> bool:
	"""Evaluate SQL-like wildcard patterns against a record value."""
	if record_value is None or expected_value is None:
		return False

	pattern = str(expected_value)
	regex_parts: list[str] = []
	for character in pattern:
		if character == "%":
			regex_parts.append(".*")
		elif character == "_":
			regex_parts.append(".")
		else:
			regex_parts.append(re.escape(character))

	regex_pattern = "^" + "".join(regex_parts) + "$"
	return re.fullmatch(regex_pattern, str(record_value)) is not None


def build_default_operator_registry() -> FilterOperatorRegistry:
	"""Create the default registry with all built-in operators registered."""
	registry = FilterOperatorRegistry()
	registry.register(EqualsOperator())
	registry.register(NotEqualsOperator())
	registry.register(GreaterThanOperator())
	registry.register(GreaterThanOrEqualOperator())
	registry.register(LessThanOperator())
	registry.register(LessThanOrEqualOperator())
	registry.register(InOperator())
	registry.register(NotInOperator())
	registry.register(LikeOperator())
	registry.register(NotLikeOperator())
	registry.register(StartsWithOperator())
	registry.register(EndsWithOperator())
	registry.register(ContainsOperator())
	registry.register(IsNullOperator())
	registry.register(IsNotNullOperator())
	return registry


DEFAULT_OPERATOR_REGISTRY = build_default_operator_registry()
