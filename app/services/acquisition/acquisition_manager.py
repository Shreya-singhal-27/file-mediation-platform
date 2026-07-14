from app.schemas.acquisition import AcquiredFile
from app.services.acquisition.base_acquisition import (
	BaseAcquisitionService,
)
from app.services.acquisition.ftp_service import FTPService
from app.services.acquisition.local_service import LocalService
from app.services.acquisition.sftp_service import SFTPService


class AcquisitionManager:
	"""
	Coordinates file acquisition from different source types.

	The manager delegates all operations to the configured
	acquisition service without exposing protocol-specific
	implementation details to the rest of the application.
	"""

	SERVICE_MAP = {
		"LOCAL": LocalService,
		"FTP": FTPService,
		"SFTP": SFTPService,
	}

	def __init__(
		self,
		source_type: str,
		config_path: str | None = None,
	):

		source_type = source_type.upper()

		if source_type not in self.SERVICE_MAP:

			raise ValueError(
				f"Unsupported acquisition source: {source_type}"
			)

		service_class = self.SERVICE_MAP[source_type]

		if config_path is None:
			self.service: BaseAcquisitionService = service_class()
		else:
			self.service = service_class(config_path)

	def connect(
		self,
	) -> None:
		"""
		Connect to the configured acquisition source.
		"""

		self.service.connect()

	def disconnect(
		self,
	) -> None:
		"""
		Close the acquisition connection.
		"""

		self.service.disconnect()

	def test_connection(
		self,
	) -> bool:
		"""
		Test whether the acquisition source is reachable.
		"""

		return self.service.test_connection()

	def fetch_files(
		self,
	) -> list[AcquiredFile]:
		"""
		Acquire all available files.
		"""

		return self.service.fetch_files()

	def archive_file(
		self,
		file: AcquiredFile,
	) -> None:
		"""
		Archive a successfully processed file.
		"""

		self.service.archive_file(file)

	def reject_file(
		self,
		file: AcquiredFile,
		reason: str,
	) -> None:
		"""
		Move a rejected file to the rejected directory.
		"""

		self.service.reject_file(
			file,
			reason,
		)

	def __enter__(
		self,
	):
		"""
		Context manager support.
		"""

		self.connect()

		return self

	def __exit__(
		self,
		exc_type,
		exc_val,
		exc_tb,
	):
		"""
		Automatically disconnect when exiting context.
		"""

		self.disconnect()