from pathlib import Path
from typing import Any

from app.services.decoder.base_decoder import BaseDecoder


class FixedWidthDecoder(BaseDecoder):
	"""
	Decoder for fixed-width text files.
	"""

	def __init__(
		self,
		column_specifications: list[
			tuple[str, int, int]
		] | None = None,
	):

		self.column_specifications = (
			column_specifications or []
		)

	@property
	def supported_extensions(
		self,
	) -> list[str]:

		return [
			".fw",
		]

	def decode(
		self,
		file_path: str | Path,
	) -> list[dict[str, Any]]:

		path = self.validate_file(
			file_path,
		)

		records: list[
			dict[str, Any]
		] = []

		with open(
			path,
			"r",
			encoding="utf-8",
		) as file:

			for line in file:

				record: dict[
					str,
					Any,
				] = {}

				for (
					field,
					start,
					end,
				) in self.column_specifications:

					record[field] = (
						line[start:end]
						.strip()
					)

				records.append(
					record,
				)

		return records