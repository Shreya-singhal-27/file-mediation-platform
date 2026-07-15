import mmap
import os

from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from app.services.decoder.base_decoder import BaseDecoder
from app.services.decoder.ber_utils import (
    VALUE_DECODERS,
    decode_ber_length,
    decode_raw,
)
from app.services.decoder.field_definition import (
    FieldDefinition,
)
from app.services.decoder.schema_parser import (
    ParsedSchema,
    parse_schema,
)


class ASN1Decoder(BaseDecoder):

    def __init__(
        self,
        schema_path: str,
        record_type: Optional[str] = None,
    ):

        self.schema_path = schema_path

        self.schema: ParsedSchema = parse_schema(
            schema_path,
        )

        if record_type is None:

            if len(self.schema.records) == 1:

                record_type = next(
                    iter(self.schema.records)
                )

            else:

                available = list(
                    self.schema.records
                )

                raise ValueError(
                    f"Schema defines {len(available)} record types: "
                    f"{available}\n"
                    "Specify record_type."
                )

        if record_type not in self.schema.records:

            raise ValueError(
                f"{record_type} not found in schema. "
                f"Available: {list(self.schema.records)}"
            )

        self.record_type: str = record_type

        self.fields: List[
            FieldDefinition
        ] = self.schema.records[
            record_type
        ]

        self.tag_map: Dict[
            int,
            FieldDefinition,
        ] = {

            field.tag_num: field

            for field in self.fields

        }

        self._fn: Dict[
            int,
            Callable,
        ] = {

            field.tag_num:

            VALUE_DECODERS.get(
                field.asn_type,
                decode_raw,
            )

            for field in self.fields

        }

    @property
    def supported_extensions(
        self,
    ) -> list[str]:

        return [
            ".dat",
        ]

    def decode(
        self,
        file_path: str | Path,
    ) -> list[dict[str, Any]]:

        return self.decode_file(
            str(file_path),
        )

    def decode_record(
        self,
        mv: memoryview,
        start: int,
        length: int,
    ) -> Dict[str, Any]:

        result: Dict[
            str,
            Any,
        ] = {}

        pos = start

        end = start + length

        while pos < end:

            tag_byte = mv[pos]

            pos += 1

            tag_class = (
                tag_byte & 0xC0
            ) >> 6

            constructed = (
                tag_byte & 0x20
            ) != 0

            tag_num = (
                tag_byte & 0x1F
            )

            if tag_num == 0x1F:

                tag_num = 0

                while True:

                    b = mv[pos]

                    pos += 1

                    tag_num = (
                        tag_num << 7
                    ) | (
                        b & 0x7F
                    )

                    if not (
                        b & 0x80
                    ):
                        break

            length_val, pos = (
                decode_ber_length(
                    mv,
                    pos,
                )
            )

            content = mv[
                pos:
                pos + length_val
            ]

            pos += length_val

            if tag_class != 2:
                continue

            field = self.tag_map.get(
                tag_num,
            )

            if field is None:

                result[
                    f"unknown_tag_{tag_num}"
                ] = bytes(
                    content
                ).hex().upper()

                continue

            decoder = self._fn[
                tag_num
            ]

            try:

                if constructed:

                    if not content:

                        result[
                            field.name
                        ] = None

                    else:

                        inner_len, inner_pos = (
                            decode_ber_length(
                                content,
                                1,
                            )
                        )

                        result[
                            field.name
                        ] = decoder(
                            content[
                                inner_pos:
                            ],
                            inner_len,
                        )

                else:

                    result[
                        field.name
                    ] = decoder(
                        content,
                        length_val,
                    )

            except Exception as exc:

                result[
                    field.name
                ] = {
                    "_error": str(exc)
                }

        return result
    
    def decode_file(self, dat_path: str) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []

        if os.path.getsize(dat_path) == 0:
            return records

        with open(dat_path, 'rb') as fh:
            with mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                mv  = memoryview(mm)
                pos = 0

                while pos < len(mv):
                    pos += 1                           
                    outer_len, pos = _decode_ber_length(mv, pos)

                    try:
                        rec = self.decode_record(mv, pos, outer_len)
                        records.append(rec)
                    except Exception as exc:
                        records.append({
                            '_decode_error': str(exc),
                            '_byte_offset':  pos,
                        })

                    pos += outer_len

                del mv  

        return records

    def to_json(self, records: List[Dict],
                out_path: Optional[str] = None, indent: int = 2) -> Optional[str]:

        text = json.dumps(records, indent=indent, ensure_ascii=False, default=str)
        if out_path:
            Path(out_path).write_text(text, encoding='utf-8')
            return None
        return text

    def to_csv(self, records: List[Dict], out_path: str) -> None:
 
        if not records:
            return
        fieldnames = [f.name for f in self.fields]
        with open(out_path, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            w.writerows(records)

    def pretty_print(self, records: List[Dict]) -> None:
        for i, rec in enumerate(records):
            print(f"\n{'─'*64}")
            print(f"  [{self.record_type}]  Record #{i + 1}")
            print(f"{'─'*64}")
            for k, v in rec.items():
                print(f"  {k:<38}  {v}")

    def schema_summary(self) -> str:

        lines = [
            f"Schema file : {self.schema_path}",
            f"Module      : {self.schema.module_name}",
            f"Record type : {self.record_type}",
            f"Field count : {len(self.fields)}",
            "",
            f"  {'Tag':>4}  {'Field Name':<38} {'ASN.1 Type':<16} {'MaxSize':>8}  Opt",
            "  " + "─" * 76,
        ]
        for field in self.fields:
            size  = str(field.max_size) if field.max_size else "—"
            opt = "Y" if f.optional else "N"
            lines.append(
                f"  [{field.tag_num:>3}]  {field.name:<38} {field.asn_type:<16} {size:>8}  {opt}"
            )
        return "\n".join(lines)

