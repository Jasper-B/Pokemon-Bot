import logging

import fastjsonschema

from modules.Config import get_config
from modules.mmf.Common import load_json_mmap

log = logging.getLogger(__name__)
config = get_config()

trainer_schema = {
    "type": "object",
    "properties": {
        "tid": {"type": "number"},
        "sid": {"type": "number"},
        "pos_x": {"type": "number"},
        "pos_y": {"type": "number"},
        "state": {"type": "number"},
        "bag_state": {"type": "number"}
    }
}

TrainerValidator = fastjsonschema.compile(trainer_schema)  # Validate the data from the mmf, sometimes it sends junk


def get_trainer():
    while True:
        try:
            trainer = load_json_mmap(4096, "bizhawk_trainer_data")["trainer"]
            if TrainerValidator(trainer):
                return trainer
        except Exception as e:
            log.debug("Failed to GetTrainer(), trying again...")
            log.debug(str(e))