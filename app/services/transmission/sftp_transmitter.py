from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.transmission.base_transmitter import BaseTransmitter, TransmissionTarget
from app.services.transmission.exceptions import TransmissionConnectionException

try:  # pragma: no cover - optional dependency
	import paramiko
except ImportError:  # pragma: no cover - optional dependency
	paramiko = None


class SFTPTransmitter(BaseTransmitter):
	"""Uploads files to an SFTP server."""

	destination_type = "SFTP"

	def transmit(self, source_path: Path, target: TransmissionTarget) -> str:
		"""Upload the file to the configured SFTP server and return the remote path."""
		if paramiko is None:
			raise TransmissionConnectionException(
				"SFTP transmission requires the 'paramiko' package to be installed."
			)

		host = self._require_config(target.config, "host")
		username = self._require_config(target.config, "username")
		password = self._require_config(target.config, "password")
		port = int(target.config.get("port", 22))
		remote_directory = str(target.config.get("remote_directory", "/"))
		remote_filename = str(target.config.get("remote_filename") or source_path.name)

		try:
			transport = paramiko.Transport((host, port))
			try:
				transport.connect(username=username, password=password)
				sftp = paramiko.SFTPClient.from_transport(transport)
				try:
					sftp.chdir(remote_directory)
					sftp.put(str(source_path), remote_filename)
				finally:
					sftp.close()
			finally:
				transport.close()
			return remote_directory.rstrip("/") + "/" + remote_filename
		except Exception as exc:
			raise TransmissionConnectionException(
				f"SFTP transmission failed: {exc}"
			) from exc

	@staticmethod
	def _require_config(config: dict[str, Any], key: str) -> str:
		"""Read a required configuration value or fail fast."""
		value = config.get(key)
		if value in (None, ""):
			raise TransmissionConnectionException(f"SFTP destination configuration must include '{key}'.")
		return str(value)
