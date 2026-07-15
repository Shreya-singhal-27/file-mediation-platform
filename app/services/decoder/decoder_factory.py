from pathlib import Path

from app.services.decoder.asn_decoder import ASN1Decoder
from app.services.decoder.base_decoder import BaseDecoder
from app.services.decoder.csv_decoder import CSVDecoder
from app.services.decoder.exceptions import (
	UnsupportedDecoderException,
)
from app.services.decoder.fixed_width_decoder import (
	FixedWidthDecoder,
)
from app.services.decoder.pipe_decoder import PipeDecoder


class DecoderFactory:

	_DECODER_MAP = {

		".dat": ASN1Decoder,

		".csv": CSVDecoder,

		".fw": FixedWidthDecoder,

		".pipe": PipeDecoder,

		".txt": PipeDecoder,

	}

	@classmethod
	def create_decoder(
		cls,
		file_path: str | Path,
		**kwargs,
	) -> BaseDecoder:

		extension = Path(
			file_path,
		).suffix.lower()

		decoder = cls._DECODER_MAP.get(
			extension,
		)

		if decoder is None:

			raise UnsupportedDecoderException(
				f"No decoder available for '{extension}'."
			)

		if decoder is ASN1Decoder:

			schema_path = kwargs.get(
				"schema_path",
			)

			record_type = kwargs.get(
				"record_type",
			)

			if schema_path is None:

				raise ValueError(
					"ASN decoder requires 'schema_path'."
				)

			return ASN1Decoder(
				schema_path=schema_path,
				record_type=record_type,
			)

		if decoder is FixedWidthDecoder:

			return FixedWidthDecoder(
				column_specifications=kwargs.get(
					"column_specifications",
					[],
				),
			)

		return decoder()

	@classmethod
	def supported_extensions(
		cls,
	) -> list[str]:

		return sorted(
			cls._DECODER_MAP.keys()
		)