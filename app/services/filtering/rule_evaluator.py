from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.schemas.filtering import FilterCondition
from app.services.filtering.exceptions import FilterEvaluationException
from app.services.filtering.operators import DEFAULT_OPERATOR_REGISTRY


@dataclass(frozen=True, slots=True)
class RuleEvaluationResult:
    """Represents the outcome of evaluating a single filter rule."""

    is_matched: bool
    field_name: str
    operator: str
    expected_value: Any
    actual_value: Any
    rule_id: str
    timestamp: datetime
    reason: str | None = None


class RuleEvaluator:
    """Evaluates exactly one filtering condition against one record."""

    def __init__(self) -> None:
        self._operator_registry = DEFAULT_OPERATOR_REGISTRY

    def evaluate(
        self,
        record: dict[str, Any],
        condition: FilterCondition,
        rule_id: str,
    ) -> RuleEvaluationResult:
        """Evaluate a single condition against a single decoded record."""
        try:
            operator = self._operator_registry.get(condition.operator)
            actual_value = record.get(condition.field_name)
            is_matched = operator.evaluate(actual_value, condition.value)
        except Exception as exc:  # pragma: no cover - converted to a controlled failure
            raise FilterEvaluationException(
                f"Failed to evaluate rule '{rule_id}' for field '{condition.field_name}'."
            ) from exc

        reason = None if is_matched else self._build_reason(condition, actual_value)
        return RuleEvaluationResult(
            is_matched=is_matched,
            field_name=condition.field_name,
            operator=condition.operator,
            expected_value=condition.value,
            actual_value=actual_value,
            rule_id=rule_id,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
        )

    @staticmethod
    def _build_reason(condition: FilterCondition, actual_value: Any) -> str:
        """Build a human-readable rejection reason for a failed rule."""
        return (
            f"Field '{condition.field_name}' with value '{actual_value}' "
            f"did not satisfy operator '{condition.operator}' "
            f"against expected value '{condition.value}'."
        )
