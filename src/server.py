import time
import struct
import chunks
import sensor
import comm


# def find_sensors(ser: Serial) -> list[sensor.Sensor]:
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


def find_sensors() -> list[sensor.Sensor]:
    responses = comm.request_whoami()
    return [
        sensor.create(resp.header.uid_src, struct.unpack("I", chunk.data)[0])
        for resp in responses
        if resp.header.func == comm.Func.RESP_WHOAMI
        for chunk in chunks.unpack(resp.data)
        if chunk.id == chunks.Id.TYPE_SENSOR
    ]


def get_inst_sensors(
    sensors: list[sensor.Sensor],
) -> tuple[sensor.Temp, sensor.TempHum, sensor.TempPress, sensor.Handle]:
    temp = sensor.Temp(1)
    temp_hum = sensor.TempHum(1)
    temp_press = sensor.TempPress(1)
    handle = sensor.Handle(1)

    for s in sensors:
        if isinstance(s, sensor.Temp):
            temp = s
        elif isinstance(s, sensor.TempHum):
            temp_hum = s
        elif isinstance(s, sensor.TempPress):
            temp_press = s
        elif isinstance(s, sensor.Handle):
            handle = s

    return (temp, temp_hum, temp_press, handle)


serials = comm.find_serials()
if not serials:
    quit()

ser = serials[0]
sensors = find_sensors()

s = get_inst_sensors(sensors)
temp_sensor, temp_hum_sensor, temp_press_sensor, handle = s

responses = comm.request_status()
for resp in responses:
    uid = resp.header.uid_src
    sens = next(s for s in sensors if s.uid == uid)
    chs = chunks.unpack(resp.data)
    sens.get_status(chs)
time.sleep(1)
