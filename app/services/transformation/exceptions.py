class TransformationException(Exception):
	"""Base exception for all transformation errors."""


class MissingSourceFieldException(TransformationException):
	"""Raised when a required source field is missing from a record."""


class ConversionException(TransformationException):
	"""Raised when a value cannot be converted into the requested target type."""


class ValidationException(TransformationException):
	"""Raised when a record fails required field or output schema validation."""


class UnsupportedTransformationTypeException(TransformationException):
	"""Raised when a transformation type is not registered."""
