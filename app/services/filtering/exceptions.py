class FilterException(Exception):
    """Base exception for all filtering errors."""


class InvalidFilterConditionException(FilterException):
    """Raised when a filtering condition is malformed or incomplete."""


class InvalidFilterGroupException(FilterException):
    """Raised when a filter group cannot be evaluated safely."""


class UnsupportedFilterOperatorException(FilterException):
    """Raised when a condition references an unknown operator."""


class FilterEvaluationException(FilterException):
    """Raised when a record cannot be evaluated against a filter rule."""
