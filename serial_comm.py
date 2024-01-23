import time
import serial
import crcmod
import struct
from enum import Enum


class Func(Enum):
    REQ_WHOAMI = 1
    RESP_WHOAMI = 2
    REQ_STATUS = 3
    RESP_STATUS = 4
    REQ_WRITE_DATA = 5
    RESP_WRITE_DATA = 6
    REQ_READ_DATA = 7
    RESP_READ_DATA = 8


def to_hex(msg: bytes) -> str:
    return ' '.join(format(x, '02x') for x in msg)


def print_hex(msg: bytes):
    print(to_hex(msg))


def aura_read(ser: serial.Serial) -> (bytes, bytes):
    resp_head = ser.read(20)
    name, counter, uid_src, uid_dst, func, data_size = struct.unpack(
        '4sIIIHH', resp_head)
    crc_size = 2
    resp_body = ser.read(data_size)
    resp_crc = ser.read(crc_size)
    return (uid_src, resp_body)


def aura_parse_chunks(data: bytes):
    start = 0
    print(f'recv data {len(resp)}:')
    print_hex(resp)
    while start != len(data):
        id, size = struct.unpack_from('HH', data, start)
        start += 4
        chunk_data = data[start:start + size]
        print('chunk')
        print(f'    id: {id}')
        print(f'    size: {size}')
        print(f'    data: {to_hex(chunk_data)}')
        start = start + size
        if size == 0:
            return


def aura_pack_add_header(
        data: bytes, uid_dst: int, func: Func) -> bytes:
    aura_pack_add_header.pack_counter += 1
    header = struct.pack(
        '4sIIIHH',
        'AURA'.encode(),
        aura_pack_add_header.pack_counter,
        main_uid,
        uid_dst,
        func.value,
        len(data))
    return header + data


def aura_pack_add_crc(data: bytes) -> bytes:
    return data + crc16(data).to_bytes(2, "little")


def aura_req_whoami() -> bytes:
    pack = bytes()
    pack = aura_pack_add_header(pack, 0, Func.REQ_WHOAMI)
    pack = aura_pack_add_crc(pack)
    return pack


def aura_req_status() -> bytes:
    pack = bytes()
    pack = aura_pack_add_header(pack, 0, Func.REQ_STATUS)
    pack = aura_pack_add_crc(pack)
    return pack


def aura_handle_req_access(offset: int, count: int) -> bytes:
    pack = aura_handle_chunk_get_access(offset, count)
    pack = aura_pack_add_header(pack, handle_uid, Func.REQ_READ_DATA)
    pack = aura_pack_add_crc(pack)
    return pack


def aura_handle_chunk_get_access(offset: int, count: int) -> bytes:
    chunk = struct.pack('BBHBB', 0x0B, 0x07, 2, offset, count)
    return chunk


def aura_handle_chunk_set_time(time: int) -> bytes:
    chunk = struct.pack('BBHI', 0x0D, 0x06, 4, time)
    return chunk


crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
handle_uid = 0
main_uid = 0
aura_pack_add_header.pack_counter = 0


ser = serial.Serial()
ser.baudrate = 19200
ser.port = 'COM17'
ser.timeout = 2
ser.open()

print()
req = aura_req_whoami()
ser.write(req)
handle_uid, resp = aura_read(ser)
aura_parse_chunks(resp)


# req = aura_handle_cmd_set_time(1, uid, 0)
# ser.write(req)
# print_hex(req)
# a, resp = aura_read(ser)
# print()
# print(f'recv data {len(resp)}:')
# print_hex(resp)
# aura_parse_chunks(resp)
# time.sleep(10)

# for i in range(10):
#     req = aura_handle_req_access(0, 4)
#     ser.write(req)
#     print_hex(req)
#     a, resp = aura_read(ser)
#     print()
#     print(f'recv data {len(resp)}:')
#     print_hex(resp)
#     aura_parse_chunks(resp)
#     time.sleep(10)

for i in range(10):
    print()
    req = aura_req_status()
    ser.write(req)
    print(f'req status')
    a, resp = aura_read(ser)
    aura_parse_chunks(resp)
    time.sleep(10)

