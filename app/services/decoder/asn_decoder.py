import re, mmap, json, csv, sys, os, time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path

@dataclass(frozen=True)
class FieldDef:
    tag_num:  int
    name:     str
    asn_type: str   
    max_size: int  
    optional: bool

@dataclass
class ParsedSchema:
    module_name: str
    records: Dict[str, List[FieldDef]] 

_TYPE_MAP: Dict[str, str] = {
    "integer":         "INTEGER",
    "ia5string":       "IA5String",
    "utf8string":      "UTF8String",
    "octet string":    "OCTET STRING",
    "octetstring":     "OCTET STRING",
    "bit string":      "BIT STRING",
    "bitstring":       "BIT STRING",
    "boolean":         "BOOLEAN",
    "null":            "NULL",
    "numericstring":   "NumericString",
    "printablestring": "PrintableString",
    "visiblestring":   "VisibleString",
    "generalizedtime": "GeneralizedTime",
    "utctime":         "UTCTime",
}

_MODULE_RE = re.compile(
    r'(?P<module>\w+)\s+DEFINITIONS'
    r'(?:\s+(?:IMPLICIT|EXPLICIT)\s+TAGS)?'
    r'\s*::=\s*BEGIN',
    re.IGNORECASE,
)

_TYPEDEF_RE = re.compile(
    r'(?P<typename>\w+)\s*::=\s*(?:SET|SEQUENCE)\s*\{',
    re.IGNORECASE | re.MULTILINE,
)

_FIELD_RE = re.compile(
    r'(?P<name>\w+)\s*'                       
    r'\[(?P<tag>\d+)\]\s+'                   
    r'(?P<type>'                              
        r'OCTET\s+STRING|BIT\s+STRING'
        r'|IA5String|UTF8String|NumericString'
        r'|PrintableString|VisibleString'
        r'|GeneralizedTime|UTCTime'
        r'|INTEGER|BOOLEAN|NULL'
    r')'
    r'(?:\s*\(SIZE\s*\(\s*\d+\s*\.\.\s*(?P<maxsize>\d+)\s*\)\s*\))?'
    r'(?:\s+(?P<optional>OPTIONAL))?',                                 
    re.IGNORECASE,
)


def _strip_asn1_comments(text: str) -> str:
    return re.sub(r'--[^\n]*', '', text)


def _extract_brace_body(text: str, pos: int) -> Tuple[str, int]:
    depth = 1
    i = pos
    while i < len(text) and depth > 0:
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1
    return text[pos: i - 1], i


def _normalize_type(raw: str) -> str:
    key = re.sub(r'\s+', ' ', raw.strip()).lower()
    return _TYPE_MAP.get(key, raw.strip())  


def parse_schema(schema_path: str) -> ParsedSchema:

    text = Path(schema_path).read_text(encoding='utf-8', errors='replace')
    text = _strip_asn1_comments(text)

    mod_m = _MODULE_RE.search(text)
    module_name = mod_m.group('module') if mod_m else 'Unknown'

    records: Dict[str, List[FieldDef]] = {}

    for td_m in _TYPEDEF_RE.finditer(text):
        typename = td_m.group('typename')
        body, _  = _extract_brace_body(text, td_m.end())

        fields: List[FieldDef] = []
        seen_tags: set = set()

        for fm in _FIELD_RE.finditer(body):
            tag = int(fm.group('tag'))
            if tag in seen_tags:
                continue            
            seen_tags.add(tag)

            fields.append(FieldDef(
                tag_num  = tag,
                name     = fm.group('name'),
                asn_type = _normalize_type(fm.group('type')),
                max_size = int(fm.group('maxsize')) if fm.group('maxsize') else 0,
                optional = fm.group('optional') is not None,
            ))

        if fields:
            records[typename] = fields

    if not records:
        raise ValueError(f"Multiple record types found: {avail}")

    return ParsedSchema(module_name=module_name, records=records)


def _dec_integer(mv: memoryview, n: int) -> int:
    return int.from_bytes(bytes(mv[:n]), 'big', signed=True)

def _dec_octet_str(mv: memoryview, n: int) -> str:
    return bytes(mv[:n]).hex().upper()

def _dec_ia5(mv: memoryview, n: int) -> str:
    return bytes(mv[:n]).decode('ascii', errors='replace')

def _dec_utf8(mv: memoryview, n: int) -> str:
    return bytes(mv[:n]).decode('utf-8', errors='replace')

def _dec_bool(mv: memoryview, n: int) -> bool:
    return mv[0] != 0 if n > 0 else False

def _dec_null(_mv: memoryview, _n: int) -> None:
    return None

def _dec_raw(mv: memoryview, n: int) -> str:
    return bytes(mv[:n]).hex().upper()


_VALUE_DECODERS: Dict[str, Callable] = {
    'INTEGER':         _dec_integer,
    'IA5String':       _dec_ia5,
    'UTF8String':      _dec_utf8,
    'OCTET STRING':    _dec_octet_str,
    'BIT STRING':      _dec_octet_str,
    'BOOLEAN':         _dec_bool,
    'NULL':            _dec_null,
    'NumericString':   _dec_ia5,
    'PrintableString': _dec_ia5,
    'VisibleString':   _dec_ia5,
    'GeneralizedTime': _dec_ia5,
    'UTCTime':         _dec_ia5,
}


def _decode_ber_length(mv: memoryview, pos: int) -> Tuple[int, int]:
    first = mv[pos]; pos += 1
    if not (first & 0x80):          
        return first, pos
    num_octets = first & 0x7F
    if num_octets == 0:
        raise ValueError("Indefinite-length BER encoding is not supported")
    return int.from_bytes(mv[pos: pos + num_octets], 'big'), pos + num_octets

class ASN1Decoder:

    def __init__(self, schema_path: str, record_type: Optional[str] = None):
        self.schema_path = schema_path
        self.schema: ParsedSchema = parse_schema(schema_path)

        if record_type is None:
            if len(self.schema.records) == 1:
                record_type = next(iter(self.schema.records))
            else:
                avail = list(self.schema.records)
                raise ValueError(
                    f"Schema defines {len(avail)} record types: {avail}\n"
                    f"Specify one: ASN1Decoder(schema, record_type='<name>')"
                )

        if record_type not in self.schema.records:
            raise ValueError(
                f"'{record_type}' not found in schema. "
                f"Available: {list(self.schema.records)}"
            )

        self.record_type: str             = record_type
        self.fields:      List[FieldDef]  = self.schema.records[record_type]

        self.tag_map: Dict[int, FieldDef] = {f.tag_num: f for f in self.fields}

        self._fn: Dict[int, Callable] = {
            f.tag_num: _VALUE_DECODERS.get(f.asn_type, _dec_raw)
            for f in self.fields
        }


    def decode_record(self, mv: memoryview, start: int, length: int) -> Dict[str, Any]:
       
        result: Dict[str, Any] = {}
        pos = start
        end = start + length

        while pos < end:
            tag_byte    = mv[pos]; pos += 1
            tag_class   = (tag_byte & 0xC0) >> 6  
            constructed = (tag_byte & 0x20) != 0
            tag_num     = tag_byte & 0x1F

            if tag_num == 0x1F:        
                tag_num = 0
                while True:
                    b = mv[pos]; pos += 1
                    tag_num = (tag_num << 7) | (b & 0x7F)
                    if not (b & 0x80):
                        break

            length_val, pos = _decode_ber_length(mv, pos)

            content = mv[pos: pos + length_val]
            pos    += length_val

            if tag_class != 2:         
                continue

            fdef = self.tag_map.get(tag_num)
            if fdef is None:
                result[f"unknown_tag_{tag_num}"] = bytes(content).hex().upper()
                continue

            fn = self._fn[tag_num]
            try:
                if constructed:
                    if not content:
                        result[fdef.name] = None
                    else:
                        inner_len, inner_pos = _decode_ber_length(content, 1)
                        result[fdef.name] = fn(content[inner_pos:], inner_len)
                else:
                    result[fdef.name] = fn(content, length_val)
            except Exception as exc:
                result[fdef.name] = {"_error": str(exc)}

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
        for f in self.fields:
            sz  = str(f.max_size) if f.max_size else "—"
            opt = "Y" if f.optional else "N"
            lines.append(
                f"  [{f.tag_num:>3}]  {f.name:<38} {f.asn_type:<16} {sz:>8}  {opt}"
            )
        return "\n".join(lines)

def main():
    import argparse

    p = argparse.ArgumentParser(description="ASN.1 BER decoder")

    p.add_argument("dat_file", nargs="?")
    p.add_argument("-s", "--schema", required=True)
    p.add_argument("-t", "--type")
    p.add_argument("-o", "--output", choices=["json", "csv", "pretty"], default="pretty")
    p.add_argument("-f", "--out-file")
    p.add_argument("--schema-info", action="store_true")

    args = p.parse_args()

    decoder = ASN1Decoder(args.schema, args.type)

    if args.schema_info:
        print(decoder.schema_summary())
        return

    if not args.dat_file:
        p.error("dat_file required")

    if not Path(args.dat_file).exists():
        sys.exit(f"File not found: {args.dat_file}")

    start = time.perf_counter()
    records = decoder.decode_file(args.dat_file)
    elapsed = (time.perf_counter() - start) * 1000

    print(f"Decoded {len(records)} record(s) in {elapsed:.2f} ms", file=sys.stderr)

    if args.output == "json":
        result = decoder.to_json(records, args.out_file)
        if result:
            print(result)

    elif args.output == "csv":
        out = args.out_file or args.dat_file.replace(
            ".dat", "_decoded.csv"
        )
        decoder.to_csv(records, out)
        print(f"Written: {out}", file=sys.stderr)

    else:
        decoder.pretty_print(records)


if __name__ == '__main__':
    main()
