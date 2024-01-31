import time
import chunks
import sensor
import comm
import log


def find_sensors() -> list[sensor.Sensor]:
    sensors = []
    uids = []
    for i in range(10):
        responses = comm.request_whoami()
        for resp in responses:
            header = resp.header
            if header.func != comm.Func.RESP_WHOAMI:
                continue
            uid = header.uid_src
            if uid not in uids:
                uids.append(uid)
                chs = chunks.unpack(resp.data)
                for chunk in chs:
                    if chunks.Id(chunk.id) == chunks.Id.TYPE_SENSOR:
                        (type_senor,) = chunk.data
                        sensors.append(sensor.create(uid, type_senor))
        time.sleep(0.5)
    return sensors


def get_inst_sensors(
    sensors: list[sensor.Sensor],
) -> tuple[sensor.Temp, sensor.TempHum, sensor.TempPress, sensor.Handle]:
    temp = sensor.Temp(0)
    temp_hum = sensor.TempHum(0)
    temp_press = sensor.TempPress(0)
    handle = sensor.Handle(0)
    for s in sensors:
        if isinstance(s, sensor.TempHum):
            temp_hum = s
        elif isinstance(s, sensor.TempPress):
            temp_press = s
        elif isinstance(s, sensor.Temp):
            temp = s
        elif isinstance(s, sensor.Handle):
            handle = s

    return (temp, temp_hum, temp_press, handle)


log.set_level(
    log.Levels.SENSOR
    | log.Levels.RESP_PACK
    # | log.Levels.RESP_CHUNK
    # | log.Levels.REQ_PACK
    # | log.Levels.REQ_CHUNK
)

if not comm.find_serials():
    quit()

sensors = find_sensors()

for s in sensors:
    print(s.NAME, hex(s.uid))

s = get_inst_sensors(sensors)
temp_sensor, temp_hum_sensor, temp_press_sensor, handle = s
# time.sleep(1)
# temp_sensor.request_temp_offset(0)
# temp_hum_sensor.request_temp_hum_offset(0, 0)
# temp_hum_sensor.request_hum_offset(20)
# temp_press_sensor.request_temp_offset(10)
# temp_press_sensor.request_temp_press_offset(0, 0)
# handle.request_access(0, 4)
handle.request_saved_cards(0, 4)
time.sleep(1)

for i in range(30000):
    responses = comm.request_status()
    for resp in responses:
        uid = resp.header.uid_src
        sens = next((s for s in sensors if s.uid == uid), None)
        if sens is None:
            print(f"Unknown uid src: {uid}")
            print(resp)
            print()
            continue
        chs = chunks.unpack(resp.data)
        sens.get_status(chs)
    time.sleep(1)
    if i % 16 == 0:
        handle.request_access(0, 4)
        time.sleep(1)
