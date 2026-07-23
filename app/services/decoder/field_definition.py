from dataclasses import dataclass
from typing import Dict
from typing import List


@dataclass(frozen=True)
class FieldDefinition:
	"""
	Represents a single ASN.1 field.
	"""

	tag_num: int

	name: str

	asn_type: str

	max_size: int

	optional: bool


@dataclass
class ParsedSchema:
	"""
	Parsed ASN.1 schema.
	"""

	module_name: str

	records: Dict[
		str,
		List[FieldDefinition],
	]