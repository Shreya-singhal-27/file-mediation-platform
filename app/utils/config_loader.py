import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ConfigLoader:
	"""
	Utility class for loading and validating JSON configuration files.
	"""

	@staticmethod
	def load(
		config_path: str | Path,
	) -> dict[str, Any]:
		"""
		Load a JSON configuration file as a dictionary.
		"""

		path = Path(config_path)

		if not path.exists():
			raise FileNotFoundError(
				f"Configuration file not found: {path}"
			)

		try:
			with open(
				path,
				"r",
				encoding="utf-8",
			) as file:
				return json.load(file)

		except json.JSONDecodeError as exc:
			raise ValueError(
				f"Invalid JSON configuration: {exc}"
			) from exc

	@staticmethod
	def load_as(
		config_path: str | Path,
		schema: type[T],
	) -> T:
		"""
		Load a JSON configuration file and validate it
		against a Pydantic schema.
		"""

		data = ConfigLoader.load(config_path)

		return schema.model_validate(data)

	@staticmethod
	def validate_keys(
		config: dict[str, Any],
		required_keys: list[str],
	) -> None:
		"""
		Validate that all required keys are present.
		Useful when a Pydantic schema is not being used.
		"""

		missing = [
			key
			for key in required_keys
			if key not in config
		]

		if missing:
			raise ValueError(
				f"Missing configuration keys: {', '.join(missing)}"
			)