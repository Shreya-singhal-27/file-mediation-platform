from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models.destination import Destination
from app.services.transmission.base_transmitter import (
	BaseTransmitter,
	TransmissionLogEntry,
	TransmissionResult,
	TransmissionTarget,
)
from app.services.transmission.exceptions import TransmissionAttemptException, TransmissionException
from app.services.transmission.sender_manager import DEFAULT_TRANSMISSION_SENDER_REGISTRY, TransmissionSenderRegistry


@dataclass(slots=True)
class TransmissionRetryPolicy:
	"""Defines retry behaviour for transmission failures."""

	attempts: int = 3
	delay_seconds: float = 0.0
	backoff_factor: float = 2.0


class TransmissionManager:
	"""Coordinates sender selection, retries, archiving, and transfer logging."""

	def __init__(
		self,
		sender_registry: TransmissionSenderRegistry | None = None,
		retry_policy: TransmissionRetryPolicy | None = None,
	) -> None:
		self._sender_registry = sender_registry or DEFAULT_TRANSMISSION_SENDER_REGISTRY
		self._retry_policy = retry_policy or TransmissionRetryPolicy()

	def transmit_file(
		self,
		source_path: str | Path,
		destination: Destination | TransmissionTarget | dict[str, Any],
		checksum_algorithm: str = "sha256",
	) -> TransmissionResult:
		"""Transmit a file to the configured destination with retry handling."""
		source_file = Path(source_path)
		target = self._normalize_destination(destination)
		sender = self._sender_registry.get(target.destination_type)
		checksum = sender.calculate_checksum(source_file, checksum_algorithm)
		max_attempts = self._resolve_attempts(target.config)

		logs: list[TransmissionLogEntry] = [
			sender.build_log("INFO", f"Starting transmission to {target.destination_type} destination '{target.name or target.destination_id or target.destination_type}'.")
		]
		last_error: str | None = None

		for attempt in range(1, max_attempts + 1):
			try:
				logs.append(sender.build_log("INFO", f"Transmission attempt {attempt} of {max_attempts}."))
				destination_path = sender.transmit(source_file, target)
				archived_path = sender.archive_source(source_file, target)
				logs.append(sender.build_log("INFO", f"Transmission succeeded on attempt {attempt}."))
				if archived_path is not None:
					logs.append(sender.build_log("INFO", f"Archived source file to '{archived_path}'."))
				return TransmissionResult(
					success=True,
					status="SUCCESS",
					source_path=source_file,
					destination_type=target.destination_type,
					destination_path=destination_path,
					checksum=checksum,
					attempts=attempt,
					archived_path=archived_path,
					logs=logs,
				)
			except Exception as exc:
				last_error = str(exc)
				logs.append(sender.build_log("ERROR", f"Attempt {attempt} failed: {exc}"))
				if attempt < max_attempts:
					time.sleep(self._retry_delay_for_attempt(target.config, attempt))

		logs.append(sender.build_log("ERROR", f"Transmission failed after {max_attempts} attempts."))
		return TransmissionResult(
			success=False,
			status="FAILED",
			source_path=source_file,
			destination_type=target.destination_type,
			destination_path=None,
			checksum=checksum,
			attempts=max_attempts,
			archived_path=None,
			logs=logs,
			error_message=last_error,
		)

	def _normalize_destination(
		self,
		destination: Destination | TransmissionTarget | dict[str, Any],
	) -> TransmissionTarget:
		"""Convert supported destination inputs into a normalized transmission target."""
		if isinstance(destination, TransmissionTarget):
			return destination

		if isinstance(destination, Destination):
			return TransmissionTarget(
				destination_type=destination.destination_type.upper(),
				config=dict(destination.config),
				name=destination.name,
				destination_id=destination.id,
			)

		destination_type = str(destination.get("destination_type") or destination.get("type") or "").upper()
		if not destination_type:
			raise TransmissionException("Destination payload must define 'destination_type'.")

		config = destination.get("config")
		if config is None:
			config = {
				key: value
				for key, value in destination.items()
				if key not in {"id", "name", "destination_type", "type"}
			}

		if not isinstance(config, dict):
			raise TransmissionException("Destination 'config' must be a dictionary when provided.")

		return TransmissionTarget(
			destination_type=destination_type,
			config=config,
			name=destination.get("name"),
			destination_id=destination.get("id"),
		)

	def _resolve_attempts(self, config: dict[str, Any]) -> int:
		"""Resolve the configured retry attempt count."""
		configured_attempts = config.get("retry_count") or config.get("retry_attempts")
		if configured_attempts is None:
			return self._retry_policy.attempts
		return max(1, int(configured_attempts))

	def _retry_delay_for_attempt(self, config: dict[str, Any], attempt: int) -> float:
		"""Resolve the delay between attempts using exponential backoff."""
		base_delay = float(config.get("retry_delay_seconds", self._retry_policy.delay_seconds))
		backoff = float(config.get("retry_backoff_factor", self._retry_policy.backoff_factor))
		if base_delay <= 0:
			return 0.0
		return base_delay * (backoff ** (attempt - 1))
