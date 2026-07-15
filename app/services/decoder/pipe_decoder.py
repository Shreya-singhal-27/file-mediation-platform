import csv
from pathlib import Path
from typing import Any

from app.services.decoder.base_decoder import BaseDecoder


class PipeDecoder(BaseDecoder):
	"""
	Decoder for pipe-delimited text files.
	"""

	@property
	def supported_extensions(
		self,
	) -> list[str]:

		return [
			".txt",
			".pipe",
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
				delimiter="|",
			)

			for row in reader:

				records.append(
					dict(row),
				)

		return records