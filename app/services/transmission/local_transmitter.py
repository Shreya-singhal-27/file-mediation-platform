from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.transmission.base_transmitter import BaseTransmitter, TransmissionTarget
from app.services.transmission.exceptions import TransmissionConnectionException
from app.utils.file_utils import FileUtils


class LocalTransmitter(BaseTransmitter):
	"""Copies files to a configured local destination directory."""

	destination_type = "LOCAL"

	def transmit(self, source_path: Path, target: TransmissionTarget) -> str:
		"""Copy the source file into the configured destination directory."""
		destination_directory = self._resolve_destination_directory(target.config)
		FileUtils.ensure_directory(destination_directory)
		destination_path = destination_directory / source_path.name

		try:
			FileUtils.copy_file(source_path, destination_path)
			return str(destination_path)
		except Exception as exc:
			raise TransmissionConnectionException(
				f"Local transmission failed: {exc}"
			) from exc

	@staticmethod
	def _resolve_destination_directory(config: dict[str, Any]) -> Path:
		"""Resolve the configured local destination directory."""
		for key in ("destination_directory", "target_directory", "local_directory", "output_directory"):
			value = config.get(key)
			if value:
				return Path(value)
		raise TransmissionConnectionException(
			"Local destination configuration must include a destination directory."
		)
