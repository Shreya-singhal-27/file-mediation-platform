import logging
from datetime import datetime
from pathlib import Path

import paramiko

from app.schemas.acquisition import AcquiredFile
from app.schemas.config import SFTPConfiguration
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


class SFTPService(BaseAcquisitionService):

	def __init__(
		self,
		config_path: str = "configs/sftp_source.json",
	):

		self.config_path = Path(config_path)

		self.transport: paramiko.Transport | None = None

		self.sftp: paramiko.SFTPClient | None = None

		self.connected = False

		self._load_configuration()

	def _load_configuration(
		self,
	) -> None:

		config = ConfigLoader.load_as(
			self.config_path,
			SFTPConfiguration,
		)

		self.host = config.host

		self.port = config.port

		self.username = config.username

		self.password = config.password

		self.remote_directory = config.remote_directory

		self.download_directory = Path(
			config.local_download_directory,
		)

		self.archive_directory = Path(
			config.archive_directory,
		)

		self.rejected_directory = Path(
			config.rejected_directory,
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
				self.download_directory,
			)

			FileUtils.ensure_directory(
				self.archive_directory,
			)

			FileUtils.ensure_directory(
				self.rejected_directory,
			)

			self.transport = paramiko.Transport(
				(self.host, self.port)
			)

			self.transport.connect(
				username=self.username,
				password=self.password,
			)

			self.sftp = paramiko.SFTPClient.from_transport(
				self.transport,
			)

			self.connected = True

			logger.info(
				"Connected to SFTP server."
			)

		except Exception as exc:

			raise ConnectionException(
				f"SFTP connection failed: {exc}"
			) from exc

	def disconnect(
		self,
	) -> None:

		if self.sftp is not None:
			self.sftp.close()

		if self.transport is not None:
			self.transport.close()

		self.connected = False

		logger.info(
			"Disconnected from SFTP."
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
				"SFTP connection not established."
			)

		acquired_files: list[AcquiredFile] = []

		try:

			self.sftp.chdir(
				self.remote_directory,
			)

			for file_attr in self.sftp.listdir_attr():

				filename = file_attr.filename

				extension = Path(
					filename,
				).suffix.lower()

				if (
					self.allowed_extensions
					and extension
					not in self.allowed_extensions
				):
					continue

				local_file = (
					self.download_directory
					/ filename
				)

				self.sftp.get(
					filename,
					str(local_file),
				)

				if FileUtils.is_empty_file(
					local_file,
				):
					continue

				acquired_files.append(

					AcquiredFile(

						filename=filename,

						path=local_file,

						source_type="SFTP",

						acquired_at=datetime.utcnow(),

						size=FileUtils.get_file_size(
							local_file,
						),

						checksum=FileUtils.calculate_checksum(
							local_file,
						),

					)

				)

			logger.info(
				"%d SFTP file(s) downloaded.",
				len(acquired_files),
			)

			return acquired_files

		except Exception as exc:

			raise FileAcquisitionException(
				str(exc)
			) from exc

	def archive_file(
		self,
		file: AcquiredFile,
	) -> None:

		try:

			FileUtils.move_file(
				file.path,
				self.archive_directory
				/ file.filename,
			)

			if self.sftp is not None:

				self.sftp.remove(
					file.filename,
				)

			logger.info(
				"%s archived.",
				file.filename,
			)

		except Exception as exc:

			raise ArchiveException(
				str(exc)
			) from exc

	def reject_file(
		self,
		file: AcquiredFile,
		reason: str,
	) -> None:

		try:

			FileUtils.move_file(
				file.path,
				self.rejected_directory
				/ file.filename,
			)

			logger.warning(
				"%s rejected. %s",
				file.filename,
				reason,
			)

		except Exception as exc:

			raise RejectFileException(
				str(exc)
			) from exc