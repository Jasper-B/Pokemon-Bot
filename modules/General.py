import logging

from modules.data.Game_state import game_state
from modules.Config import get_config
from modules.Image import detect_template
from modules.Inputs import button_combo, hold_button, press_button, release_all_inputs, wait_frames
from modules.Menuing import start_menu
from modules.Navigation import bonk, follow_path
from modules.Stats import encounter_pokemon, opponent_changed
from modules.mmf.Trainer import get_trainer

log = logging.getLogger(__name__)
config = get_config()

# Mode to run between specific coordinates
def mode_coords():
    coords = config["coords"]
    pos1, pos2 = coords["pos1"], coords["pos2"]
    while True:
        while not opponent_changed():
            follow_path([(pos1[0], pos1[1]), (pos2[0], pos2[1])])
        encounter_pokemon()
        while get_trainer()["state"] != game_state.OVERWORLD:
            continue

# mode to run until bonking
def mode_bonk():
    direction = config["direction"].lower()

    while True:
        log.info(f"Pathing {direction} until bonk...")

        while True: #not OpponentChanged():
            if direction == "horizontal":
                pos1 = bonk("Left")
                pos2 = bonk("Right")
            else:
                pos1 = bonk("Up")
                pos2 = bonk("Down")
            if pos1 == pos2:
                continue

            follow_path([pos1, pos2])

        #EncounterPokemon()

        #while GetTrainer()["state"] != GameState.OVERWORLD:
        #    continue