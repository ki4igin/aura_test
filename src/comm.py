from serial import Serial
import crcmod
import struct
import chunks

# import sensor
from enum import Enum
from typing import NamedTuple
from tools import to_hex
import serial.tools.list_ports as list_ports


__serial = Serial()
__counter = 0
__server_uid = 1234


class Func(Enum):
    REQ_WHOAMI = 1
    RESP_WHOAMI = 2
    REQ_STATUS = 3
    RESP_STATUS = 4
    REQ_WRITE_DATA = 5
    RESP_WRITE_DATA = 6
    REQ_READ_DATA = 7
    RESP_READ_DATA = 8


class Header(NamedTuple):
    protocol: bytes
    counter: int
    uid_src: int
    uid_dst: int
    func: Func
    data_size: int

    def __str__(self):
        return (
            f"protocol : {self.protocol}\n"
            f"counter  : {self.counter}\n"
            f"uid src  : {self.uid_src}\n"
            f"uid dst  : {self.uid_dst}\n"
            f"func     : {self.func}\n"
            f"data size: {self.data_size}"
        )


class Package(NamedTuple):
    header: Header
    data: bytes
    crc: int


class PackageRaw(NamedTuple):
    header: bytes
    data: bytes
    crc: bytes

    def __str__(self) -> str:
        return (
            f"head: {to_hex(self.header)}\n"
            f"data: {to_hex(self.data)}\n"
            f"crc : {to_hex(self.crc)}"
        )


def pack_read() -> Package | None:
    resp_header = __serial.read(20)
    if len(resp_header) != 20:
        return None
    header = Header._make(struct.unpack("4sIIIHH", resp_header))
    resp_data = __serial.read(header.data_size)
    resp_crc = __serial.read(2)
    resp = PackageRaw(resp_header, resp_data, resp_crc)
    print("pack resp:")
    print(resp)
    (crc,) = struct.unpack("H", resp_crc)
    if crc16(resp_header + resp_data) != crc:
        print("crc error")
    return Package(header, resp_data, crc)


def pack_create(uid_dst: int, func: Func, data: bytes = bytes()) -> bytes:
    global __counter
    __counter += 1
    header = struct.pack(
        "4sIIIHH",
        "AURA".encode(),
        __counter,
        __server_uid,
        uid_dst,
        func.value,
        len(data),
    )
    body = header + data
    return body + struct.pack("H", crc16(body))


def request(uid: int, func: Func, *chs: chunks.Chunk | None) -> list[Package]:
    data = chunks.pack(*[ch for ch in chs if ch is not None])
    package = pack_create(uid, func, data)
    __serial.open()
    __serial.write(package)
    resp = get_responses()
    __serial.close()
    return resp


def request_whoami() -> list[Package]:
    return request(0, Func.REQ_WHOAMI, None)


def request_status() -> list[Package]:
    return request(0, Func.REQ_STATUS, None)


def find_serials() -> None:
    global __serial
    ports = list_ports.comports()
    if not ports:
        print("COM ports not found")

    for p in ports:
        print(f"finding devices on {p.name}...")
        __serial = Serial(port=p.name, baudrate=19200, timeout=0.5)
        __serial.close()
        __serial.open()
        responses = request_whoami()
        if not responses or responses[0].header.protocol != "AURA":
            print(f"no AURA devices found on {p.name}")
        else:
            print(f"AURA devices found on {p.name}")
            __serial.close()
            return
        __serial.close()


# def request_sensor_temp_offset(
#     ser: Serial,
#     sensor: sensor.Temp,
#     offset: float,
# ) -> list[Package]:
#     chunk = sensor.create_chunk_temp_offset(offset)
#     return request(ser, uid, Func.REQ_WRITE_DATA, chunk)


# def request_sensor_hum_offset(
#     ser: Serial,
#     sensor: sensor.TempHum,
#     offset: float,
# ) -> list[Package]:
#     chunk = sensor.create_chunk_hum_offset(offset)
#     return request(ser, uid, Func.REQ_WRITE_DATA, chunk)


# def request_sensor_press_offset(
#     ser: Serial,
#     sensor: sensor.TempPress,
#     offset: float,
# ) -> list[Package]:
#     chunk = sensor.create_chunk_press_offset(offset)
#     return request(ser, uid, Func.REQ_WRITE_DATA, chunk)


def get_responses() -> list[Package]:
    responses = []
    while package := pack_read():
        responses.append(package)
    return responses


crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
