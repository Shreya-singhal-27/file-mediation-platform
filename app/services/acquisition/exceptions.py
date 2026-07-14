class AcquisitionException(Exception):
	"""
	Base exception for all acquisition-related errors.
	"""

	pass


class ConnectionException(AcquisitionException):
	"""
	Unable to connect to acquisition source.
	"""

	pass


class FileAcquisitionException(AcquisitionException):
	"""
	Failed while acquiring a file.
	"""

	pass


class ArchiveException(AcquisitionException):
	"""
	Failed while archiving a processed file.
	"""

	pass


class RejectFileException(AcquisitionException):
	"""
	Failed while moving a rejected file.
	"""

	pass