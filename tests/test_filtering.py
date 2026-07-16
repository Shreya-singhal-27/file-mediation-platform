"""Tests for the filtering module."""

from app.schemas.filtering import FilterCondition, FilterGroup
from app.services.filtering.base_filter import FilterRuleDefinition
from app.services.filtering.filter_manager import FilterManager


def test_filter_manager_filters_records_using_simple_condition() -> None:
    """Records matching a simple condition should be accepted."""
    manager = FilterManager()
    records = [
        {"name": "alice", "age": 30},
        {"name": "bob", "age": 20},
    ]

    result = manager.filter_records(
        records,
        [
            FilterCondition(
                rule_id="age-check",
                field_name="age",
                operator=">=",
                value=25,
            )
        ],
    )

    assert result.statistics.total_records == 2
    assert result.statistics.accepted_records == 1
    assert result.statistics.rejected_records == 1
    assert result.accepted_records == [{"name": "alice", "age": 30}]
    assert result.rejected_records[0].rule_id == "age-check"


def test_filter_manager_supports_or_groups() -> None:
    """A record should pass when any condition in an OR group matches."""
    manager = FilterManager()
    records = [
        {"name": "alice", "country": "KE"},
        {"name": "bob", "country": "UG"},
    ]

    result = manager.filter_records(
        records,
        [
            FilterGroup(
                logical_operator="OR",
                conditions=[
                    FilterCondition(field_name="country", operator="=", value="KE"),
                    FilterCondition(field_name="name", operator="=", value="carol"),
                ],
            )
        ],
    )

    assert result.statistics.accepted_records == 1
    assert result.statistics.rejected_records == 1
    assert result.accepted_records[0]["name"] == "alice"


def test_filter_manager_preserves_rejection_metadata() -> None:
    """Rejected records should carry the original payload, rule id, and reason."""
    manager = FilterManager()
    records = [{"msisdn": "12345", "status": "inactive"}]

    result = manager.filter_records(
        records,
        [
            FilterRuleDefinition(
                rule_id="status-rule",
                rule=FilterCondition(field_name="status", operator="=", value="active"),
                priority=1,
            )
        ],
    )

    rejected_record = result.rejected_records[0]
    assert rejected_record.original_record == {"msisdn": "12345", "status": "inactive"}
    assert rejected_record.rule_id == "status-rule"
    assert "status" in rejected_record.reject_reason
