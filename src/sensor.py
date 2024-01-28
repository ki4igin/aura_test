from enum import Enum
from chunks import Chunk
from typing import NamedTuple
from tools import print_with_indent, to_hex, add_indent


class Type(Enum):
    LM75BD = 1
    TMP112 = 2
    SHT30 = 3
    ZS05 = 4
    BMP180 = 5
    LPS22HB = 6
    HANDLE = 7
    EXPANDER = 8
    LEAK = 9


class Sensor:
    NAME = "Sensor"
    uid: int
    status: NamedTuple

    def __init__(self, uid: int):
        self.uid = uid

    def get_status(self, chunks: list[Chunk]):
        self.parse_status(chunks)
        print(f"{self.NAME}:")
        print_with_indent(self.status)

    def parse_status(self, chunks: list[Chunk]):
        raise NotImplementedError("Subclasses must implement parse_status()")


class TempSensor(Sensor):
    class Id(Enum):
        TEMPERATURE = 0x04

    class Status(NamedTuple):
        temperature: float

        def __str__(self) -> str:
            return f"temp: {self.temperature:04.1f} ℃"

    NAME = "Temperature sensor"
    status: Status = Status(0)

    def parse_status(self, chunks: list[Chunk]):
        (temp,) = self.status
        for ch in chunks:
            match ch.id:
                case self.Id.TEMPERATURE:
                    temp = ch.data

        self.status = self.Status(temp)


class TempHumSensor(Sensor):
    class Id(Enum):
        TEMPERATURE = 0x04
        HUMIDITY = 0x05

    class Status(NamedTuple):
        temperature: float
        humidity: float

        def __str__(self) -> str:
            temp, hum = self
            return f"temp: {temp:04.1f} ℃; hum: {hum:02.0f} %"

    NAME = "Temperature and humidity sensor"
    status: Status = Status(0, 0)

    def parse_status(self, chunks: list[Chunk]):
        temp, hum = self.status
        for ch in chunks:
            match ch.id:
                case self.Id.TEMPERATURE:
                    temp = ch.data
                case self.Id.HUMIDITY:
                    hum = ch.data
        self.status = self.Status(temp, hum)


class TempPressSensor(Sensor):
    class Id(Enum):
        TEMPERATURE = 0x04
        PRESSURE = 0x06

    class Status(NamedTuple):
        temperature: float
        pressure: float

        def __str__(self) -> str:
            temp, press = self
            return f"temp: {temp:04.1f} ℃; press: {press:06.0f} Па"

    NAME = "Temperature and pressure sensor"
    status: Status = Status(0, 0)

    def parse_status(self, chunks: list[Chunk]):
        temp, press = self.status
        for ch in chunks:
            match ch.id:
                case self.Id.TEMPERATURE:
                    temp = ch.data
                case self.Id.PRESSURE:
                    press = ch.data
        self.status = self.Status(temp, press)


class Access(NamedTuple):
    card_uid: bytes
    time: int
    is_valid: bool

    def __str__(self) -> str:
        return (
            f"card : {to_hex(self.card_uid)}\n"
            f"time : {self.time} sec\n"
            f"valid: {self.is_valid}"
        )


class Handle(Sensor):
    class Id(Enum):
        ERR = 3
        STATUS_LOCKER = 4
        CARD_UID = 5
        CARD_UID_ARR_WRITE = 6
        CARD_UID_ARR_READ = 7
        CARD_RANGE = 8
        CARD_SAVE_COUNT = 9
        CARD_CLEAR = 10
        ACCESS_COUNT = 11
        ACCESS_IS_VALID = 12
        ACCESS_TIME = 13

    class Status(NamedTuple):
        lock: bool
        last_access: Access

        def __str__(self) -> str:
            (lock, last_access) = self
            return (
                f"locker: {'open' if lock else 'close'}\n"
                f"last access:\n"
                f"{add_indent(last_access.__str__())}"
            )

    NAME = "Handle"
    status: Status

    def parse_status(self, chunks: list[Chunk]):
        (lock, (card_uid, time, is_valid)) = self.status
        for ch in chunks:
            match ch.id:
                case self.Id.STATUS_LOCKER:
                    self.status_lock = ch.data == 0x00FF
                case self.Id.CARD_UID:
                    card_uid = ch.data
                case self.Id.ACCESS_TIME:
                    time = ch.data
                case self.Id.ACCESS_IS_VALID:
                    is_valid = ch.data == 0x00FF

        self.last_access = self.Status(lock, Access(card_uid, time, is_valid))


def create(uid: int, type: int):
    match type:
        case Type.LM75BD | Type.TMP112:
            return TempSensor(uid)
        case Type.SHT30 | Type.ZS05:
            return TempHumSensor(uid)
        case Type.BMP180 | Type.LPS22HB:
            return TempPressSensor(uid)
        case Type.HANDLE:
            return Handle(uid)
        # case Type.EXPANDER:
        #     return Expander(uid)
        # case Type.LEAK:
        #     return Leak(uid)
        case _:
            return Sensor(uid)
