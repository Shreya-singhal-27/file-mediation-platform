from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from app.models.filter_rule import FilterRule
from app.schemas.filtering import FilterCondition, FilterGroup, FilterResult
from app.services.filtering.base_filter import FilterRuleDefinition
from app.services.filtering.filter_engine import FilterEngine
from app.utils.coercion import coerce_value


class FilterManager:
    """Normalizes configurable filter inputs and delegates execution to the engine."""

    def __init__(self, filter_engine: FilterEngine | None = None) -> None:
        self._filter_engine = filter_engine or FilterEngine()

    def filter_records(
        self,
        records: list[dict[str, Any]],
        rules: Sequence[FilterRule | FilterRuleDefinition | FilterCondition | FilterGroup | dict[str, Any]],
    ) -> FilterResult:
        """Apply the configured rules to a batch of decoded records."""
        normalized_rules = self._normalize_rules(rules)
        return self._filter_engine.filter(records, normalized_rules)

    def _normalize_rules(
        self,
        rules: Sequence[FilterRule | FilterRuleDefinition | FilterCondition | FilterGroup | dict[str, Any]],
    ) -> list[FilterRuleDefinition]:
        """Convert supported rule inputs into engine-ready rule definitions."""
        normalized_rules: list[FilterRuleDefinition] = []

        for index, rule in enumerate(rules, start=1):
            if isinstance(rule, FilterRuleDefinition):
                normalized_rules.append(rule)
                continue

            if isinstance(rule, FilterCondition):
                normalized_rules.append(
                    FilterRuleDefinition(
                        rule_id=rule.rule_id or rule.field_name,
                        rule=rule,
                        priority=index,
                    )
                )
                continue

            if isinstance(rule, FilterGroup):
                normalized_rules.append(
                    FilterRuleDefinition(
                        rule_id=f"group-{index}",
                        rule=rule,
                        priority=index,
                    )
                )
                continue

            if isinstance(rule, FilterRule):
                normalized_rules.append(self._from_orm_rule(rule, priority=index))
                continue

            normalized_rules.append(self._from_mapping(rule, priority=index))

        return normalized_rules

    def _from_orm_rule(self, rule: FilterRule, priority: int) -> FilterRuleDefinition:
        """Convert a SQLAlchemy filter rule model into an engine definition."""
        condition = FilterCondition(
            field_name=rule.field_name,
            operator=rule.operator,
            value=coerce_value(rule.value),
        )
        return FilterRuleDefinition(
            rule_id=str(rule.id),
            rule=condition,
            priority=rule.priority or priority,
        )

    def _from_mapping(self, rule: dict[str, Any], priority: int) -> FilterRuleDefinition:
        """Convert a mapping payload into an engine definition."""
        rule_id = str(rule.get("rule_id") or rule.get("id") or priority)
        field_name = rule.get("field_name")
        operator = rule.get("operator")

        if field_name is None or operator is None:
            raise ValueError("Filter rule mappings must define 'field_name' and 'operator'.")

        condition = FilterCondition(
            field_name=str(field_name),
            operator=str(operator),
            value=coerce_value(rule.get("value")),
        )
        return FilterRuleDefinition(
            rule_id=rule_id,
            rule=condition,
            priority=int(rule.get("priority", priority)),
        )
