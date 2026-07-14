import logging
from datetime import datetime
from pathlib import Path

from app.schemas.acquisition import AcquiredFile
from app.schemas.config import SourceConfiguration
from app.services.acquisition.base_acquisition import (
	BaseAcquisitionService,
)
from app.services.acquisition.exceptions import (
	ArchiveException,
	ConnectionException,
	FileAcquisitionException,
	RejectFileException,
)
from app.utils.config_loader import ConfigLoader
from app.utils.file_utils import FileUtils


logger = logging.getLogger(__name__)


class LocalService(BaseAcquisitionService):

	def __init__(
		self,
		config_path: str = "configs/source.json",
	):

		self.config_path = Path(config_path)

		self.connected = False

		self._load_configuration()

	def _load_configuration(
		self,
	) -> None:

		config = ConfigLoader.load_as(
			self.config_path,
			SourceConfiguration,
		)

		self.source_directory = Path(
			config.source_path,
		)

		self.archive_directory = Path(
			config.archive_path,
		)

		self.rejected_directory = Path(
			config.rejected_path,
		)

		self.allowed_extensions = {
			extension.lower()
			for extension in config.allowed_extensions
		}

	def connect(
		self,
	) -> None:

		try:

			FileUtils.ensure_directory(
				self.source_directory,
			)

			FileUtils.ensure_directory(
				self.archive_directory,
			)

			FileUtils.ensure_directory(
				self.rejected_directory,
			)

			self.connected = True

			logger.info(
				"Connected to local acquisition source: %s",
				self.source_directory,
			)

		except Exception as exc:

			raise ConnectionException(
				f"Failed to connect to local source: {exc}"
			) from exc

	def disconnect(
		self,
	) -> None:

		self.connected = False

		logger.info(
			"Disconnected from local acquisition source."
		)

	def test_connection(
		self,
	) -> bool:

		try:

			self.connect()

			self.disconnect()

			return True

		except Exception:

			return False

	def fetch_files(
		self,
	) -> list[AcquiredFile]:

		if not self.connected:

			raise ConnectionException(
				"Local source is not connected."
			)

		acquired_files: list[AcquiredFile] = []

		try:

			for file in FileUtils.list_files(
				self.source_directory,
			):

				if (
					self.allowed_extensions
					and FileUtils.get_extension(file)
					not in self.allowed_extensions
				):
					continue

				if FileUtils.is_empty_file(
					file,
				):
					logger.warning(
						"Skipping empty file: %s",
						file.name,
					)
					continue

				acquired_files.append(

					AcquiredFile(

						filename=file.name,

						path=file,

						source_type="LOCAL",

						acquired_at=datetime.utcnow(),

						size=FileUtils.get_file_size(
							file,
						),

						checksum=FileUtils.calculate_checksum(
							file,
						),

					)

				)

			logger.info(
				"Successfully acquired %d file(s).",
				len(acquired_files),
			)

			return acquired_files

		except Exception as exc:

			raise FileAcquisitionException(
				f"Failed to acquire files: {exc}"
			) from exc

	def archive_file(
		self,
		file: AcquiredFile,
	) -> None:

		try:

			FileUtils.move_file(
				file.path,
				self.archive_directory / file.filename,
			)

			logger.info(
				"Archived file: %s",
				file.filename,
			)

		except Exception as exc:

			raise ArchiveException(
				f"Failed to archive '{file.filename}': {exc}"
			) from exc

	def reject_file(
		self,
		file: AcquiredFile,
		reason: str,
	) -> None:

		try:

			FileUtils.move_file(
				file.path,
				self.rejected_directory / file.filename,
			)

			logger.warning(
				"Rejected file '%s'. Reason: %s",
				file.filename,
				reason,
			)

		except Exception as exc:

			raise RejectFileException(
				f"Failed to reject '{file.filename}': {exc}"
			) from exc