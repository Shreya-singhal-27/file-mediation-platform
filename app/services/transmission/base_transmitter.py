from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar, Literal

from app.utils.file_utils import FileUtils


TransferLevel = Literal["INFO", "WARNING", "ERROR"]
TransferStatus = Literal["SUCCESS", "FAILED"]


@dataclass(slots=True)
class TransmissionTarget:
	"""Normalized destination details used by transmission strategies."""

	destination_type: str
	config: dict[str, Any]
	name: str | None = None
	destination_id: int | None = None


@dataclass(slots=True)
class TransmissionLogEntry:
	"""Represents one timestamped transfer log entry."""

	timestamp: datetime
	level: TransferLevel
	message: str


@dataclass(slots=True)
class TransmissionResult:
	"""Captures the outcome of a transmission attempt or retry sequence."""

	success: bool
	status: TransferStatus
	source_path: Path
	destination_type: str
	destination_path: str | None = None
	checksum: str | None = None
	attempts: int = 0
	archived_path: Path | None = None
	logs: list[TransmissionLogEntry] = field(default_factory=list)
	error_message: str | None = None


class BaseTransmitter(ABC):
	"""Defines the contract shared by all protocol-specific transmitters."""

	destination_type: ClassVar[str]

	@abstractmethod
	def transmit(self, source_path: Path, target: TransmissionTarget) -> str:
		"""Transfer the source file and return the resulting destination path."""

	def archive_source(self, source_path: Path, target: TransmissionTarget) -> Path | None:
		"""Archive a successfully transmitted file when an archive directory is configured."""
		archive_directory = self._get_path_config(target.config, "archive_directory", "archive_path")
		if archive_directory is None:
			return None

		archive_directory.mkdir(parents=True, exist_ok=True)
		archive_path = archive_directory / source_path.name
		FileUtils.move_file(source_path, archive_path)
		return archive_path

	@staticmethod
	def build_log(level: TransferLevel, message: str) -> TransmissionLogEntry:
		"""Create a timestamped transfer log entry."""
		return TransmissionLogEntry(
			timestamp=datetime.now(timezone.utc),
			level=level,
			message=message,
		)

	@staticmethod
	def calculate_checksum(source_path: Path, algorithm: str = "sha256") -> str:
		"""Calculate a checksum for the file being transmitted."""
		return FileUtils.calculate_checksum(source_path, algorithm=algorithm)

	@staticmethod
	def _get_path_config(config: dict[str, Any], *keys: str) -> Path | None:
		"""Return the first configured path-like value found in the target configuration."""
		for key in keys:
			value = config.get(key)
			if value:
				return Path(value)
		return None
