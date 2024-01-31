import struct
import log
from enum import Enum
from typing import NamedTuple, Any


class DataType(Enum):
    NONE = 0
    I8 = 1
    U8 = 2
    I16 = 3
    U16 = 4
    I32 = 5
    U32 = 6
    F32 = 7
    f64 = 8
    STR = 9
    I8_ARR = 10
    U8_ARR = 11
    I16_ARR = 12
    U16_ARR = 13
    I32_ARR = 14
    U32_ARR = 15
    F32_ARR = 16
    f64_ARR = 17
    CARD_UID = 19
    CARD_UID_ARR = 20
    CARD_RANGE = 21


def type2format(type: DataType, size: int = 0) -> str:
    type_mapping = {
        DataType.NONE: "x",
        DataType.I8: "b",
        DataType.U8: "B",
        DataType.I16: "h",
        DataType.U16: "H",
        DataType.I32: "i",
        DataType.U32: "I",
        DataType.F32: "f",
        DataType.f64: "d",
        DataType.STR: "s",
        DataType.I8_ARR: f"{size}b",
        DataType.U8_ARR: f"{size}B",
        DataType.I16_ARR: f"{size // 2}h",
        DataType.U16_ARR: f"{size // 2}H",
        DataType.I32_ARR: f"{size // 4}i",
        DataType.U32_ARR: f"{size // 4}I",
        DataType.F32_ARR: f"{size // 4}f",
        DataType.f64_ARR: f"{size // 8}d",
        DataType.CARD_UID: "Q",
        DataType.CARD_UID_ARR: f"{size // 8}Q",
        DataType.CARD_RANGE: "BB",
    }
    return type_mapping.get(type, "") if size != 0 else ""


class Id(Enum):
    TYPE_SENSOR = 0x01
    UIDS_ARRAY = 0x02


class Chunk(NamedTuple):
    id: int
    type: DataType
    data_size: int
    data: tuple[Any, ...] | Any

    def __str__(self) -> str:
        return (
            f"id  : {self.id:02x}\n"
            f"type: {self.type}\n"
            f"size: {self.data_size}\n"
            f"data: {self.data}"
        )


def unpack(data: bytes) -> list[Chunk]:
    CHUNK_HEADER_SIZE = 4
    start = 0
    chunks = []
    while start < len(data):
        id, type, size = struct.unpack_from("BBH", data, start)
        type = DataType(type)
        start += CHUNK_HEADER_SIZE
        val = struct.unpack_from(type2format(type, size), data, start)
        start += size
        chunk = Chunk(id, type, size, val)
        log.resp_chunk(chunk)
        chunks.append(chunk)
    return chunks


def pack(*chunks: Chunk) -> bytes:
    res = bytes()
    for chunk in chunks:
        log.req_chunk(chunk)
        id, type, size, data = chunk
        format = "BBH" + type2format(type, size)
        data = data if isinstance(data, (list, tuple)) else (data,)
        res += struct.pack(format, id, type.value, size, *data)
    return res
