import csv
from pathlib import Path
from typing import Any

from app.services.decoder.base_decoder import BaseDecoder


class CSVDecoder(BaseDecoder):
	"""
	Decoder for CSV files.
	"""

	@property
	def supported_extensions(
		self,
	) -> list[str]:

		return [
			".csv",
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
			newline="",
			encoding="utf-8",
		) as file:

			reader = csv.DictReader(
				file,
			)

			for row in reader:

				records.append(
					dict(row),
				)

		return records