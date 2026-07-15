from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any


class BaseDecoder(ABC):
	"""
	Base interface implemented by every decoder.

	Every decoder converts an input file into a list of
	normalized Python dictionaries that can be consumed
	by the filtering and transformation modules.
	"""

	@abstractmethod
	def decode(
		self,
		file_path: str | Path,
	) -> list[dict[str, Any]]:
		"""
		Decode an input file.

		Args:
			file_path:
				Path of the file to decode.

		Returns:
			List of decoded records.
		"""
		pass

	@property
	@abstractmethod
	def supported_extensions(
		self,
	) -> list[str]:
		"""
		File extensions supported by this decoder.
		"""
		pass

	def validate_file(
		self,
		file_path: str | Path,
	) -> Path:
		"""
		Common validation used by all decoders.
		"""

		path = Path(file_path)

		if not path.exists():

			raise FileNotFoundError(
				f"File not found: {path}"
			)

		if not path.is_file():

			raise ValueError(
				f"{path} is not a file."
			)

		if path.suffix.lower() not in self.supported_extensions:

			raise ValueError(
				f"Unsupported file type: {path.suffix}"
			)

		return path