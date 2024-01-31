from enum import Flag, auto
from tools import add_indent

# from comm import PackageRaw


class Levels(Flag):
    REQ_PACK = auto()
    RESP_PACK = auto()
    REQ_CHUNK = auto()
    RESP_CHUNK = auto()
    SENSOR = auto()


level_init = Levels.SENSOR


def resp_chunk(value: object):
    header = "resp chunk:"
    text = add_indent(value.__str__())
    log(Levels.RESP_CHUNK, f"{header}\n{text}\n")


def resp_pack(value, is_valid: bool = True):
    header = f"resp pack ({len(value)}):"
    text = value.__str__()
    crc = "" if is_valid else "\ncrc_error"
    log(Levels.RESP_PACK, f"{header}\n{text}{crc}\n")


def req_pack(value):
    header = f"req pack ({len(value)}):"
    text = value.__str__()
    log(Levels.REQ_PACK, f"{header}\n{text}\n")


def req_chunk(value: object):
    header = "req chunk:"
    text = add_indent(value.__str__())
    log(Levels.REQ_CHUNK, f"{header}\n{text}\n")


def sensor(*value: object):
    log(Levels.SENSOR, *value)


def log(level, *value: object):
    if level in level_init:
        print(*value)


def set_level(level: Levels):
    global level_init
    level_init = level
