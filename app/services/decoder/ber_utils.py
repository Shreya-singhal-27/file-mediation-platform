from typing import Any, Callable, Dict, Tuple


def _dec_integer(mv: memoryview, n: int) -> int:
    return int.from_bytes(bytes(mv[:n]), "big", signed=True)


def _dec_octet_str(mv: memoryview, n: int) -> str:
    return bytes(mv[:n]).hex().upper()


def _dec_ia5(mv: memoryview, n: int) -> str:
    return bytes(mv[:n]).decode(
        "ascii",
        errors="replace",
    )


def _dec_utf8(mv: memoryview, n: int) -> str:
    return bytes(mv[:n]).decode(
        "utf-8",
        errors="replace",
    )


def _dec_bool(
    mv: memoryview,
    n: int,
) -> bool:
    return mv[0] != 0 if n > 0 else False


def _dec_null(
    _mv: memoryview,
    _n: int,
) -> None:
    return None


def _dec_raw(
    mv: memoryview,
    n: int,
) -> str:
    return bytes(mv[:n]).hex().upper()


VALUE_DECODERS: Dict[str, Callable] = {

    "INTEGER": _dec_integer,

    "IA5String": _dec_ia5,

    "UTF8String": _dec_utf8,

    "OCTET STRING": _dec_octet_str,

    "BIT STRING": _dec_octet_str,

    "BOOLEAN": _dec_bool,

    "NULL": _dec_null,

    "NumericString": _dec_ia5,

    "PrintableString": _dec_ia5,

    "VisibleString": _dec_ia5,

    "GeneralizedTime": _dec_ia5,

    "UTCTime": _dec_ia5,
}


def decode_ber_length(
    mv: memoryview,
    pos: int,
) -> Tuple[int, int]:

    first = mv[pos]

    pos += 1

    if not (first & 0x80):

        return first, pos

    num_octets = first & 0x7F

    if num_octets == 0:

        raise ValueError(
            "Indefinite-length BER encoding is not supported"
        )

    return (
        int.from_bytes(
            mv[pos : pos + num_octets],
            "big",
        ),
        pos + num_octets,
    )