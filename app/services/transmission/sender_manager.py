from __future__ import annotations

from typing import Any, ClassVar

from app.services.transmission.base_transmitter import BaseTransmitter
from app.services.transmission.exceptions import UnsupportedDestinationTypeException
from app.services.transmission.ftp_transmitter import FTPTransmitter
from app.services.transmission.local_transmitter import LocalTransmitter
from app.services.transmission.sftp_transmitter import SFTPTransmitter


class TransmissionSenderRegistry:
	"""Resolves transmitter implementations by destination type."""

	def __init__(self) -> None:
		self._senders: dict[str, BaseTransmitter] = {}

	def register(self, sender: BaseTransmitter) -> None:
		"""Register a transmitter implementation."""
		self._senders[sender.destination_type.upper()] = sender

	def get(self, destination_type: str) -> BaseTransmitter:
		"""Return the registered transmitter for a destination type."""
		sender = self._senders.get(destination_type.upper())
		if sender is None:
			raise UnsupportedDestinationTypeException(
				f"Unsupported destination type '{destination_type}'."
			)
		return sender

	def available(self) -> list[str]:
		"""Return all supported destination types."""
		return sorted(self._senders.keys())


def build_default_sender_registry() -> TransmissionSenderRegistry:
	"""Create the default registry with built-in transmitters registered."""
	registry = TransmissionSenderRegistry()
	registry.register(LocalTransmitter())
	registry.register(FTPTransmitter())
	registry.register(SFTPTransmitter())
	return registry


DEFAULT_TRANSMISSION_SENDER_REGISTRY = build_default_sender_registry()
