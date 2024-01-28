import time
import serial
import serial.tools.list_ports as list_ports
import crcmod
import struct
import chunks
import sensor
from enum import Enum
from typing import NamedTuple
from tools import to_hex


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


def pack_read(ser: serial.Serial) -> Package | None:
    resp_header = ser.read(20)
    if len(resp_header) != 20:
        return None
    header = Header._make(struct.unpack("4sIIIHH", resp_header))
    resp_data = ser.read(header.data_size)
    resp_crc = ser.read(2)
    resp = PackageRaw(resp_header, resp_data, resp_crc)
    print("pack resp:")
    print(resp)
    (crc,) = struct.unpack("H", resp_crc)
    if crc16(resp_header + resp_data) != crc:
        print("crc error")
    return Package(header, resp_data, crc)


def pack_create(uid_dst: int, func: Func, data: bytes = bytes()) -> bytes:
    pack_create.counter += 1
    header = struct.pack(
        "4sIIIHH",
        "AURA".encode(),
        pack_create.counter,
        pack_create.server_uid,
        uid_dst,
        func.value,
        len(data),
    )
    body = header + data
    return body + struct.pack("H", crc16(body))


pack_create.counter = 0
pack_create.server_uid = 0


def request_whoami(ser: serial.Serial) -> list[Package]:
    pack = pack_create(0, Func.REQ_WHOAMI)
    ser.write(pack)
    return get_responses(ser)


def request_status(ser: serial.Serial) -> list[Package]:
    pack = pack_create(0, Func.REQ_STATUS)
    ser.write(pack)
    return get_responses(ser)


def get_responses(ser: serial.Serial) -> list[Package]:
    responses = []
    while package := pack_read(ser):
        responses.append(package)
    return responses


def find_serials() -> list[serial.Serial]:
    serials = []
    ports = list_ports.comports()
    if not ports:
        print("COM ports not found")

    for p in ports:
        print(f"finding devices on {p.name}...")
        ser = serial.Serial(port=p.name, baudrate=19200, timeout=0.5)
        ser.close()
        ser.open()
        responses = request_whoami(ser)
        if not responses or responses[0].header.protocol != "AURA":
            print(f"no AURA devices found on {p.name}")
        else:
            serials.append(ser)
            print(f"AURA devices found on {p.name}")
        ser.close()

    return serials


# def find_sensors(ser: serial.Serial) -> list[sensor.Sensor]:
#     responses = request_whoami(ser)
#     sensors = []
#     for resp in responses:
#         header = resp.header
#         if header.func != Func.RESP_WHOAMI:
#             continue
#         uid = header.uid_src
#         chs = chunks.parse(resp.data)
#         for chunk in chs:
#             if chunk.id == chunks.Id.TYPE_SENSOR:
#                 (sensor_type,) = struct.unpack("I", chunk.data)
#                 sensors.append(sensor.create(uid, sensor_type))
#     return sensors


def find_sensors(ser: serial.Serial) -> list[sensor.Sensor]:
    responses = request_whoami(ser)
    return [
        sensor.create(resp.header.uid_src, struct.unpack("I", chunk.data)[0])
        for resp in responses
        if resp.header.func == Func.RESP_WHOAMI
        for chunk in chunks.parse(resp.data)
        if chunk.id == chunks.Id.TYPE_SENSOR
    ]


crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
serials = find_serials()
if not serials:
    quit()

ser = serials[0]
sensors = find_sensors(ser)

responses = request_status(ser)
for resp in responses:
    uid = resp.header.uid_src
    sens = next(s for s in sensors if s.uid == uid)
    chs = chunks.parse(resp.data)
    sens.get_status(chs)
time.sleep(1)
