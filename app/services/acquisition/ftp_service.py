import logging
from datetime import datetime
from ftplib import FTP
from pathlib import Path

from app.schemas.acquisition import AcquiredFile
from app.schemas.config import FTPConfiguration
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


class FTPService(BaseAcquisitionService):

	def __init__(
		self,
		config_path: str = "configs/ftp_source.json",
	):

		self.config_path = Path(config_path)

		self.ftp: FTP | None = None

		self.connected = False

		self._load_configuration()

	def _load_configuration(
		self,
	) -> None:

		config = ConfigLoader.load_as(
			self.config_path,
			FTPConfiguration,
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
			ext.lower()
			for ext in config.allowed_extensions
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

			self.ftp = FTP()

			self.ftp.connect(
				self.host,
				self.port,
			)

			self.ftp.login(
				self.username,
				self.password,
			)

			self.ftp.cwd(
				self.remote_directory,
			)

			self.connected = True

			logger.info(
				"Connected to FTP server."
			)

		except Exception as exc:

			raise ConnectionException(
				f"FTP connection failed: {exc}"
			) from exc

	def disconnect(
		self,
	) -> None:

		if self.ftp is not None:

			self.ftp.quit()

		self.connected = False

		logger.info(
			"Disconnected from FTP."
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
				"FTP connection not established."
			)

		acquired_files: list[AcquiredFile] = []

		try:

			for filename in self.ftp.nlst():

				extension = Path(filename).suffix.lower()

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

				with open(
					local_file,
					"wb",
				) as file:

					self.ftp.retrbinary(
						f"RETR {filename}",
						file.write,
					)

				if FileUtils.is_empty_file(
					local_file,
				):
					continue

				acquired_files.append(

					AcquiredFile(

						filename=filename,

						path=local_file,

						source_type="FTP",

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
				"%d FTP files downloaded.",
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

			if self.ftp is not None:

				self.ftp.delete(
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