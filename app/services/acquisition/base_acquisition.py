from abc import ABC, abstractmethod

from app.schemas.acquisition import AcquiredFile


class BaseAcquisitionService(ABC):
	"""
	Base interface for all acquisition services.

	Each acquisition service (LOCAL, FTP, SFTP)
	must implement the methods defined here.
	"""

	@abstractmethod
	def connect(self) -> None:
		"""
		Establish a connection to the source.
		"""
		pass

	@abstractmethod
	def disconnect(self) -> None:
		"""
		Close the connection gracefully.
		"""
		pass

	@abstractmethod
	def fetch_files(
		self,
	) -> list[AcquiredFile]:
		"""
		Retrieve all available files from the configured source.
		"""
		pass

	@abstractmethod
	def archive_file(
		self,
		file: AcquiredFile,
	) -> None:
		"""
		Move a successfully processed file
		to the archive location.
		"""
		pass

	@abstractmethod
	def reject_file(
		self,
		file: AcquiredFile,
		reason: str,
	) -> None:
		"""
		Move an invalid file to the rejected folder.
		"""
		pass

	@abstractmethod
	def test_connection(
		self,
	) -> bool:
		"""
		Verify that the configured source
		can be reached successfully.
		"""
		pass