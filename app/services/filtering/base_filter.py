from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.schemas.filtering import (
    FilterCondition,
    FilterGroup,
    FilterResult,
    FilterStatistics,
    RejectedRecord,
)
from app.services.filtering.rule_evaluator import RuleEvaluationResult, RuleEvaluator


@dataclass(frozen=True, slots=True)
class FilterRuleDefinition:
    """Binds a configurable rule payload to a stable rule identifier."""

    rule_id: str
    rule: FilterCondition | FilterGroup
    priority: int = 1


class BaseFilter(ABC):
    """Defines the shared contract and helpers for filtering components."""

    def __init__(self, rule_evaluator: RuleEvaluator | None = None) -> None:
        self._rule_evaluator = rule_evaluator or RuleEvaluator()

    @abstractmethod
    def filter(
        self,
        records: list[dict[str, Any]],
        rules: list[FilterRuleDefinition],
    ) -> FilterResult:
        """Filter a batch of decoded records and return the full outcome."""

    @staticmethod
    def _build_rejected_record(
        original_record: dict[str, Any],
        evaluation_result: RuleEvaluationResult,
    ) -> RejectedRecord:
        """Convert a failed evaluation into a rejected record payload."""
        return RejectedRecord(
            original_record=original_record,
            reject_reason=evaluation_result.reason or "Record did not satisfy the filter rule.",
            rule_id=evaluation_result.rule_id,
            timestamp=evaluation_result.timestamp,
        )

    @staticmethod
    def _build_result(
        accepted_records: list[dict[str, Any]],
        rejected_records: list[RejectedRecord],
    ) -> FilterResult:
        """Build a normalized filtering result with summary statistics."""
        statistics = FilterStatistics(
            total_records=len(accepted_records) + len(rejected_records),
            accepted_records=len(accepted_records),
            rejected_records=len(rejected_records),
        )
        return FilterResult(
            accepted_records=accepted_records,
            rejected_records=rejected_records,
            statistics=statistics,
        )
