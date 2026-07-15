class DecoderException(Exception):
	"""
	Base exception for all decoder errors.
	"""

	pass


class SchemaParseException(DecoderException):
	"""
	Raised when an ASN schema cannot be parsed.
	"""

	pass


class BERDecodeException(DecoderException):
	"""
	Raised when BER decoding fails.
	"""

	pass


class InvalidRecordException(DecoderException):
	"""
	Raised when a malformed record is encountered.
	"""

	pass


class UnsupportedDecoderException(DecoderException):
	"""
	Raised when no decoder exists for a file type.
	"""

	pass