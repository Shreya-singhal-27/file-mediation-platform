import re
from pathlib import Path
from typing import Dict
from typing import List
from typing import Tuple

from app.services.decoder.field_definition import (
	FieldDefinition,
	ParsedSchema,
)


_TYPE_MAP: Dict[str, str] = {
	"integer": "INTEGER",
	"ia5string": "IA5String",
	"utf8string": "UTF8String",
	"octet string": "OCTET STRING",
	"octetstring": "OCTET STRING",
	"bit string": "BIT STRING",
	"bitstring": "BIT STRING",
	"boolean": "BOOLEAN",
	"null": "NULL",
	"numericstring": "NumericString",
	"printablestring": "PrintableString",
	"visiblestring": "VisibleString",
	"generalizedtime": "GeneralizedTime",
	"utctime": "UTCTime",
}


_MODULE_RE = re.compile(
	r"(?P<module>\w+)\s+DEFINITIONS"
	r"(?:\s+(?:IMPLICIT|EXPLICIT)\s+TAGS)?"
	r"\s*::=\s*BEGIN",
	re.IGNORECASE,
)


_TYPEDEF_RE = re.compile(
	r"(?P<typename>\w+)\s*::=\s*(?:SET|SEQUENCE)\s*\{",
	re.IGNORECASE | re.MULTILINE,
)


_FIELD_RE = re.compile(
	r"(?P<name>\w+)\s*"
	r"\[(?P<tag>\d+)\]\s+"
	r"(?P<type>"
	r"OCTET\s+STRING|BIT\s+STRING"
	r"|IA5String|UTF8String|NumericString"
	r"|PrintableString|VisibleString"
	r"|GeneralizedTime|UTCTime"
	r"|INTEGER|BOOLEAN|NULL"
	r")"
	r"(?:\s*\(SIZE\s*\(\s*\d+\s*\.\.\s*(?P<maxsize>\d+)\s*\)\s*\))?"
	r"(?:\s+(?P<optional>OPTIONAL))?",
	re.IGNORECASE,
)


def strip_asn1_comments(
	text: str,
) -> str:

	return re.sub(
		r"--[^\n]*",
		"",
		text,
	)


def extract_brace_body(
	text: str,
	pos: int,
) -> Tuple[str, int]:

	depth = 1

	index = pos

	while index < len(text) and depth > 0:

		if text[index] == "{":

			depth += 1

		elif text[index] == "}":

			depth -= 1

		index += 1

	return text[pos : index - 1], index


def normalize_type(
	raw: str,
) -> str:

	key = re.sub(
		r"\s+",
		" ",
		raw.strip(),
	).lower()

	return _TYPE_MAP.get(
		key,
		raw.strip(),
	)


def parse_schema(
	schema_path: str,
) -> ParsedSchema:

	text = Path(
		schema_path,
	).read_text(
		encoding="utf-8",
		errors="replace",
	)

	text = strip_asn1_comments(
		text,
	)

	module_match = _MODULE_RE.search(
		text,
	)

	module_name = (
		module_match.group("module")
		if module_match
		else "Unknown"
	)

	records: Dict[
		str,
		List[FieldDefinition],
	] = {}

	for type_match in _TYPEDEF_RE.finditer(
		text,
	):

		type_name = type_match.group(
			"typename",
		)

		body, _ = extract_brace_body(
			text,
			type_match.end(),
		)

		fields: List[
			FieldDefinition
		] = []

		seen_tags = set()

		for field_match in _FIELD_RE.finditer(
			body,
		):

			tag = int(
				field_match.group(
					"tag",
				)
			)

			if tag in seen_tags:
				continue

			seen_tags.add(
				tag,
			)

			fields.append(

				FieldDefinition(

					tag_num=tag,

					name=field_match.group(
						"name",
					),

					asn_type=normalize_type(
						field_match.group(
							"type",
						)
					),

					max_size=(
						int(
							field_match.group(
								"maxsize",
							)
						)
						if field_match.group(
							"maxsize",
						)
						else 0
					),

					optional=(
						field_match.group(
							"optional",
						)
						is not None
					),

				)

			)

		if fields:

			records[
				type_name
			] = fields

	if not records:

		raise ValueError(
			"No ASN.1 record definitions found."
		)

	return ParsedSchema(

		module_name=module_name,

		records=records,

	)