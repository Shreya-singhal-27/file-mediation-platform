from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class AcquiredFile(BaseModel):
	"""
	Represents a file successfully acquired from a source.
	This object is passed to the Decoder layer.
	"""

	model_config = ConfigDict(
		arbitrary_types_allowed=True,
	)

	filename: str

	path: Path

	source_type: str

	acquired_at: datetime

	size: int

	checksum: str | None = None

	job_id: int | None = None