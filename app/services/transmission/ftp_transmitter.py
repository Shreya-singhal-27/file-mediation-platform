from __future__ import annotations

from ftplib import FTP
from pathlib import Path
from typing import Any

from app.services.transmission.base_transmitter import BaseTransmitter, TransmissionTarget
from app.services.transmission.exceptions import TransmissionConnectionException


class FTPTransmitter(BaseTransmitter):
	"""Uploads files to an FTP server."""

	destination_type = "FTP"

	def transmit(self, source_path: Path, target: TransmissionTarget) -> str:
		"""Upload the file to the configured FTP server and return the remote path."""
		host = self._require_config(target.config, "host")
		username = self._require_config(target.config, "username")
		password = self._require_config(target.config, "password")
		port = int(target.config.get("port", 21))
		remote_directory = str(target.config.get("remote_directory", "/"))
		remote_filename = str(target.config.get("remote_filename") or source_path.name)

		try:
			with FTP() as ftp:
				ftp.connect(host, port)
				ftp.login(username, password)
				ftp.cwd(remote_directory)
				with open(source_path, "rb") as stream:
					ftp.storbinary(f"STOR {remote_filename}", stream)
			return remote_directory.rstrip("/") + "/" + remote_filename
		except Exception as exc:
			raise TransmissionConnectionException(
				f"FTP transmission failed: {exc}"
			) from exc

	@staticmethod
	def _require_config(config: dict[str, Any], key: str) -> str:
		"""Read a required configuration value or fail fast."""
		value = config.get(key)
		if value in (None, ""):
			raise TransmissionConnectionException(f"FTP destination configuration must include '{key}'.")
		return str(value)
