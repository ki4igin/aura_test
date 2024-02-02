from enum import Enum
from chunks import Chunk, DataType, unpack
from typing import NamedTuple
from tools import add_indent
import comm
import log


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
        log.sensor(f"{self.NAME} {hex(self.uid)}:")
        log.sensor(add_indent(self.status.__str__()))
        log.sensor()

    def parse_status(self, chunks: list[Chunk]):
        raise NotImplementedError("Subclasses must implement parse_status()")


class Temp(Sensor):
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
            match self.Id(ch.id):
                case self.Id.TEMPERATURE:
                    (temp,) = ch.data

        self.status = self.Status(temp)

    def request_temp_offset(self, offset: float) -> list[comm.Package]:
        chunk = Chunk(self.Id.TEMPERATURE.value, DataType.F32, 4, offset)
        return comm.request(self.uid, comm.Func.REQ_WRITE_DATA, chunk)


class TempHum(Temp):
    class Id(Enum):
        TEMPERATURE = 0x04
        HUMIDITY = 0x05

    class Status(NamedTuple):
        temperature: float
        humidity: float

        def __str__(self) -> str:
            temp, hum = self
            return f"temp: {temp:04.1f} ℃ hum: {hum:02.0f} %"

    NAME = "Temperature and humidity sensor"
    status: Status = Status(0, 0)

    def parse_status(self, chunks: list[Chunk]):
        temp, hum = self.status
        for ch in chunks:
            match self.Id(ch.id):
                case self.Id.TEMPERATURE:
                    temp = ch.data[0]
                case self.Id.HUMIDITY:
                    hum = ch.data[0]
        self.status = self.Status(temp, hum)

    def request_temp_hum_offset(
        self, temp_offset: float, hum_offset: float
    ) -> list[comm.Package]:
        chunk1 = Chunk(self.Id.TEMPERATURE.value, DataType.F32, 4, temp_offset)
        chunk2 = Chunk(self.Id.HUMIDITY.value, DataType.F32, 4, hum_offset)
        return comm.request(self.uid, comm.Func.REQ_WRITE_DATA, chunk1, chunk2)

    def request_hum_offset(self, offset: float) -> list[comm.Package]:
        chunk = Chunk(self.Id.HUMIDITY.value, DataType.F32, 4, offset)
        return comm.request(self.uid, comm.Func.REQ_WRITE_DATA, chunk)


class TempPress(Temp):
    class Id(Enum):
        TEMPERATURE = 0x04
        PRESSURE = 0x06

    class Status(NamedTuple):
        temperature: float
        pressure: float

        def __str__(self) -> str:
            temp, press = self
            return f"temp: {temp:04.1f} ℃ press: {press:06.0f} Па"

    NAME = "Temperature and pressure sensor"
    status: Status = Status(0, 0)

    def parse_status(self, chunks: list[Chunk]):
        temp, press = self.status
        for ch in chunks:
            match self.Id(ch.id):
                case self.Id.TEMPERATURE:
                    (temp,) = ch.data
                case self.Id.PRESSURE:
                    (press,) = ch.data
        self.status = self.Status(temp, press)

    def request_press_offset(self, offset: float) -> list[comm.Package]:
        chunk = Chunk(self.Id.PRESSURE.value, DataType.F32, 4, offset)
        return comm.request(self.uid, comm.Func.REQ_WRITE_DATA, chunk)

    def request_temp_press_offset(
        self, temp_offset: float, press_offset: float
    ) -> list[comm.Package]:
        chunk1 = Chunk(self.Id.TEMPERATURE.value, DataType.F32, 4, temp_offset)
        chunk2 = Chunk(self.Id.PRESSURE.value, DataType.F32, 4, press_offset)
        return comm.request(self.uid, comm.Func.REQ_WRITE_DATA, chunk1, chunk2)


class Access(NamedTuple):
    card_uid: int
    time: int
    is_valid: bool

    def __str__(self) -> str:
        return (
            f"card : {hex(self.card_uid)}\n"
            f"time : {self.time} sec\n"
            f"valid: {self.is_valid}"
        )


class Handle(Sensor):
    class Id(Enum):
        ERR = 3

        STATUS_LOCKER = 4

        SAVED_CARDS = 5
        SAVED_CARD_COUNT = 6
        CLEAR_SAVED_CARD = 7

        ACCESS = 8
        ACCESS_CARD = 9
        ACCESS_VALID = 10
        ACCESS_TIME = 11

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
    status: Status = Status(False, Access(0, 0, False))

    def parse_status(self, chunks: list[Chunk]):
        (lock, (card_uid, time, is_valid)) = self.status
        for ch in chunks:
            match self.Id(ch.id):
                case self.Id.STATUS_LOCKER:
                    lock = ch.data == 0x00FF
                case self.Id.ACCESS_CARD:
                    (card_uid,) = ch.data
                case self.Id.ACCESS_TIME:
                    (time,) = ch.data
                case self.Id.ACCESS_VALID:
                    is_valid = ch.data == 0x00FF
        self.status = self.Status(lock, Access(card_uid, time, is_valid))

    def parse_read(self, chunks: list[Chunk]):
        card_uid, time, is_valid = 0, 0, False
        access_mask = 0
        for ch in chunks:
            match self.Id(ch.id):
                case self.Id.ACCESS_CARD:
                    (card_uid,) = ch.data
                    access_mask |= 0b001
                case self.Id.ACCESS_TIME:
                    (time,) = ch.data
                    access_mask |= 0b010
                case self.Id.ACCESS_VALID:
                    is_valid = ch.data[0] == 0x00FF
                    access_mask |= 0b100
                case self.Id.SAVED_CARD_COUNT:
                    cards = ch.data
                    log.sensor("saved cards:")
                    if cards == 0:
                        log.sensor("cards not found")
                    elif isinstance(cards, int):
                        log.sensor(add_indent(hex(cards)))
                    else:
                        for uid in ch.data:
                            log.sensor(add_indent(hex(uid)))
                    log.sensor("")

            if access_mask == 0b111:
                access_mask = 0
                access = Access(card_uid, time, is_valid)
                log.sensor(add_indent(access.__str__()))
                log.sensor()

    def request_access(self, offset: int, count: int) -> None:
        chunk = Chunk(
            self.Id.ACCESS.value, DataType.CARD_RANGE, 2, (offset, count)
        )
        resp = comm.request(self.uid, comm.Func.REQ_READ_DATA, chunk)
        if resp:
            chunks = unpack(resp[0].data)
            self.parse_read(chunks)

    def request_saved_cards(self, offset: int, count: int) -> None:
        chunk = Chunk(
            self.Id.SAVED_CARDS.value,
            DataType.CARD_RANGE,
            2,
            (offset, count),
        )
        resp = comm.request(self.uid, comm.Func.REQ_READ_DATA, chunk)[0].data
        chunks = unpack(resp)
        self.parse_read(chunks)


class Expander(Sensor):
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
        status: bool = True

        def __str__(self) -> str:
            return f"status: {'ok' if self.status else 'dis'}"

    NAME = "Expander"
    status: Status = Status(True)

    def parse_status(self, chunks: list[Chunk]):
        pass


def create(uid: int, type: int):
    match Type(type):
        case Type.LM75BD | Type.TMP112:
            return Temp(uid)
        case Type.SHT30 | Type.ZS05:
            return TempHum(uid)
        case Type.BMP180 | Type.LPS22HB:
            return TempPress(uid)
        case Type.HANDLE:
            return Handle(uid)
        case Type.EXPANDER:
            return Expander(uid)
        # case Type.LEAK:
        #     return Leak(uid)
        case _:
            return Sensor(uid)
