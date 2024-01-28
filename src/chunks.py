import struct
from enum import Enum
from typing import NamedTuple, Any
from tools import print_with_indent


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


types_dict = {
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
    DataType.CARD_UID: "8B",
}


class Id(Enum):
    TYPE_SENSOR = 0x01
    UIDS_ARRAY = 0x02


class Chunk(NamedTuple):
    id: int
    type: DataType
    data_size: int
    data: Any

    def __str__(self) -> str:
        return (
            f"id  : {self.id:02x}\n"
            f"type: {self.type}\n"
            f"size: {self.data_size}\n"
            f"data: {self.data}"
        )


CHUNK_HEADER_SIZE = 4


def parse(data: bytes) -> list[Chunk]:
    start = 0
    chunks = []
    while start < len(data):
        id, type, size = struct.unpack_from("BBH", data, start)
        type = DataType(type)
        start += CHUNK_HEADER_SIZE
        (val,) = struct.unpack_from(types_dict[type], data, start)
        start += size
        chunk = Chunk(id, type, size, val)
        print("chunk:")
        print_with_indent(chunk)
        chunks.append(chunk)
    return chunks
