import time
import serial
import crcmod
import struct


def to_hex(msg: bytes) -> str:
    return ' '.join(format(x, '02x') for x in msg)


def print_hex(msg: bytes):
    print(to_hex(msg))


def aura_read(ser: serial.Serial) -> (bytes, bytes):
    resp_head = ser.read(20)
    name, counter, uid_src, uid_dst, func, data_size = struct.unpack(
        '4sI4s4sHH', resp_head)
    crc_size = 2
    resp_body = ser.read(data_size)
    resp_crc = ser.read(crc_size)
    return (uid_src, resp_body)


def aura_parse_chunks(data: bytes):
    start = 0
    while start != len(data):
        id, size = struct.unpack_from('HH', data, start)
        start += 4
        chunk_data = data[start:start + size]
        print('chunk')
        print(f' id: {id}')
        print(f' size: {size}')
        print(f' data: {to_hex(chunk_data)}')
        start = start + size
        if size == 0:
            return


def aura_handle_cmd_get_access(
        counter: int, handle_uid: bytes, offset: int, count: int) -> bytes:
    chunk = struct.pack('BBHBB', 0x0B, 0x07, 2, offset, count)
    size = len(chunk)
    main_uid = bytes([0x11, 0x22, 0x33, 0x44])
    header = struct.pack(
        '4sI4s4sHH',
        'AURA'.encode(),
        counter,
        main_uid,
        handle_uid,
        7,
        size)
    body = header + chunk
    return body + crc16(body).to_bytes(2, "little")


crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)

# whoami
cmd_whoami = bytearray('AURA'.encode())
cmd_whoami.extend(bytearray([1]))
cmd_whoami.extend(bytearray(3))
cmd_whoami.extend(bytearray(4))
cmd_whoami.extend(bytearray(4))
# cmd_whoami.extend(bytearray([0xd6,0x5e, 0x9b, 0x4f])) #temp sens id
# 1 - whoami, 3 - data
cmd_whoami.extend(bytearray([1]))
cmd_whoami.extend(bytearray(1))
cmd_whoami.extend(bytearray(2))
cmd_whoami.extend(crc16(cmd_whoami).to_bytes(2, 'little'))

# data req
cmd_data = bytearray('AURA'.encode())
cmd_data.extend(bytearray([1]))
cmd_data.extend(bytearray(3))
cmd_data.extend(bytearray(4))
cmd_data.extend(bytearray(4))
# 1 - whoami, 3 - data
cmd_data.extend(bytearray([3]))
cmd_data.extend(bytearray(1))
cmd_data.extend(bytearray(2))
cmd_data.extend(crc16(cmd_data).to_bytes(2, 'little'))

# write req for handle
cmd_write = bytearray('AURA'.encode())
cmd_write.extend(bytearray([1]))
cmd_write.extend(bytearray(3))
cmd_write.extend(bytearray(4))
# temp sens id
# cmd_write.extend(bytearray([0xd6, 0x5e, 0x9b, 0x4f]))
# id of handle
cmd_write.extend(bytearray([206, 55, 172, 45]))
# 1 - whoami, 3 - data, 5 - write req
cmd_write.extend(bytearray([7]))
cmd_write.extend(bytearray(1))
cmd_write.extend(bytearray(2))
cmd_write.extend(crc16(cmd_write).to_bytes(2, 'little'))

# write req for expander
cmd_write_exp = bytearray('AURA'.encode())
cmd_write_exp.extend(bytearray([1]))
cmd_write_exp.extend(bytearray(3))
cmd_write_exp.extend(bytearray(4))
# id of expander
cmd_write_exp.extend(bytearray([97, 52, 232, 28]))
# 1 - whoami, 3 - data, 5 - write req
cmd_write_exp.extend(bytearray([5, 0]))
cmd_write_exp.extend(bytearray([6, 0]))
cmd_write_exp.extend(bytearray([4, 4, 2, 0]))
cmd_write_exp.extend(bytearray([0, 0]))
cmd_write_exp.extend(crc16(cmd_write_exp).to_bytes(2, 'little'))


ser = serial.Serial()
ser.baudrate = 19200
ser.port = 'COM20'
ser.timeout = 2
ser.open()

ser.write(cmd_whoami)
print('send:')
print_hex(cmd_whoami)
# whoami from temp sens
uid, resp = aura_read(ser)
print('recv who:')
print_hex(uid)
print_hex(resp)

# ser.write (cmd_whoami)
# ser.write(crc16(cmd_whoami).to_bytes(2,'little'))
# for i in range(10):
#     ser.write(cmd_data)
#     # whoami from temp sens
#     a, resp = aura_read(ser)
#     print()
#     print('recv data:')
#     print_hex(resp)
#     aura_parse_chunks(resp)
#     time.sleep(10)

for i in range(10):
    req = aura_handle_cmd_get_access(1, uid, 0, 1)
    ser.write(req)
    a, resp = aura_read(ser)
    print()
    print(f'recv data {len(resp)}:')
    print_hex(resp)
    aura_parse_chunks(resp)
    time.sleep(10)


# for i in range(2):
#     if i%2 == 0:
#         ser.write(cmd_whoami)
#         print('whoami expander')
#         resp  = ser.read(30) #whoami from expander
#         print(' '.join(format(x, '02x') for x in resp))
#         for k in range(2):
#             print('whoami sensor', k)
#             resp  = ser.read(20+8+8+2) #whoami from sensor
#             print(' '.join(format(x, '02x') for x in resp))

#     else:
#         ser.write(cmd_data)

#         print('data expander')
#         resp  = ser.read(20)
#         print(' '.join(format(x, '02x') for x in resp))
#         resp  = ser.read(6)
#         print(' '.join(format(x, '02x') for x in resp))
#         resp  = ser.read(6)
#         print(' '.join(format(x, '02x') for x in resp))
#         resp  = ser.read(6)
#         print(' '.join(format(x, '02x') for x in resp))
#         resp  = ser.read(6)
#         print(' '.join(format(x, '02x') for x in resp))
#         resp  = ser.read(2)
#         print(' '.join(format(x, '02x') for x in resp))

#         for r in range(2):
#             print('data sensor', r)
#             resp  = ser.read(20 + 2*8 + 2)
#             print(' '.join(format(x, '02x') for x in resp))
