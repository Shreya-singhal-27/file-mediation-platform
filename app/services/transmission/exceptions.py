class TransmissionException(Exception):
	"""Base exception for all transmission errors."""


class UnsupportedDestinationTypeException(TransmissionException):
	"""Raised when a destination type is not supported by the registry."""


class TransmissionConnectionException(TransmissionException):
	"""Raised when a protocol-level connection fails."""


class TransmissionAttemptException(TransmissionException):
	"""Raised when a send operation fails during a retry attempt."""


class TransmissionArchiveException(TransmissionException):
	"""Raised when archiving a successfully transmitted file fails."""
