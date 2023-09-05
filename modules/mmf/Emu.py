import logging

import fastjsonschema

from modules.Config import get_config
from modules.mmf.Common import load_json_mmap

log = logging.getLogger(__name__)
config = get_config()

emu_schema = {
    "type": "object",
    "properties": {
        "frameCount": {"type": "number"},
        "emuFPS": {"type": "number"},
        "rngState": {"type": "number"}
    }
}

EmuValidator = fastjsonschema.compile(emu_schema)  # Validate the data from the mmf, sometimes it sends junk

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


def get_emu():
    while True:
        try:
            emu = load_json_mmap(4096, "bizhawk_emu_data")["emu"]
            if EmuValidator(emu):
                emu["speed"] = clamp(emu["emuFPS"] / 60, 0.06, 1000)
                return emu
        except Exception as e:
            log.debug("Failed to GetEmu(), trying again...")
            log.debug(str(e))