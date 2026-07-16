from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.schemas.filtering import FilterCondition, FilterGroup, FilterResult, RejectedRecord
from app.services.filtering.base_filter import BaseFilter, FilterRuleDefinition
from app.services.filtering.exceptions import InvalidFilterGroupException
from app.services.filtering.rule_evaluator import RuleEvaluationResult


@dataclass(frozen=True, slots=True)
class GroupEvaluationOutcome:
    """Represents the outcome of evaluating a condition group."""

    is_matched: bool
    reason: str | None = None


class FilterEngine(BaseFilter):
    """Evaluates multiple configurable filtering rules against decoded records."""

    def filter(
        self,
        records: list[dict[str, Any]],
        rules: list[FilterRuleDefinition],
    ) -> FilterResult:
        """Filter decoded records using the provided ordered rule set."""
        accepted_records: list[dict[str, Any]] = []
        rejected_records: list[RejectedRecord] = []
        ordered_rules = sorted(rules, key=lambda rule: rule.priority)

        for record in records:
            record_rejected = False

            for rule_definition in ordered_rules:
                outcome = self._evaluate_definition(
                    record,
                    rule_definition.rule,
                    rule_definition.rule_id,
                )
                if outcome.is_matched:
                    continue

                rejected_records.append(
                    RejectedRecord(
                        original_record=deepcopy(record),
                        reject_reason=outcome.reason or "Record did not satisfy the filter rule.",
                        rule_id=rule_definition.rule_id,
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                record_rejected = True
                break

            if not record_rejected:
                accepted_records.append(record)

        return self._build_result(accepted_records, rejected_records)

    def _evaluate_definition(
        self,
        record: dict[str, Any],
        definition: FilterCondition | FilterGroup,
        rule_id: str,
    ) -> GroupEvaluationOutcome:
        """Evaluate either a single condition or a nested condition group."""
        if isinstance(definition, FilterCondition):
            evaluation_result = self._rule_evaluator.evaluate(record, definition, rule_id=rule_id)
            return GroupEvaluationOutcome(
                is_matched=evaluation_result.is_matched,
                reason=evaluation_result.reason,
            )

        if not definition.conditions:
            raise InvalidFilterGroupException("Filter groups must contain at least one condition.")

        outcomes = [self._evaluate_definition(record, condition, rule_id) for condition in definition.conditions]
        if definition.logical_operator == "AND":
            first_failure = next((outcome for outcome in outcomes if not outcome.is_matched), None)
            if first_failure is not None:
                return first_failure
            return GroupEvaluationOutcome(is_matched=True)

        if definition.logical_operator == "OR":
            if any(outcome.is_matched for outcome in outcomes):
                return GroupEvaluationOutcome(is_matched=True)

            failure_reasons = [outcome.reason for outcome in outcomes if outcome.reason]
            combined_reason = "; ".join(failure_reasons) if failure_reasons else None
            return GroupEvaluationOutcome(is_matched=False, reason=combined_reason)

        raise InvalidFilterGroupException(
            f"Unsupported logical operator '{definition.logical_operator}' in filter group."
        )
