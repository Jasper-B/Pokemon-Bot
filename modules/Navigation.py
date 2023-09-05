import logging
import os

from modules.Inputs import hold_button, press_button, release_all_inputs, release_button, wait_frames
from modules.Stats import encounter_pokemon, opponent_changed
from modules.mmf.Emu import get_emu
from modules.mmf.Trainer import get_trainer

emu = get_emu()

def bonk(direction: str, run: bool = True):
    """
    Function to run until trainer position stops changing
    :param direction: Direction to move
    :param run: Boolean value of whether to run
    :return: Last known player coordinates or None if in a battle
    """
    press_button("B")  # press and release B in case of a random pokenav call

    hold_button(direction)
    last_x = get_trainer()["pos_x"]
    last_y = get_trainer()["pos_y"]

    move_speed = 8 if run else 16

    dir_unchanged = 0
    while dir_unchanged < move_speed:
        if run:
            hold_button("B")
            wait_frames(1)

        trainer = get_trainer()
        if last_x == trainer["pos_x"] and last_y == trainer["pos_y"]:
            dir_unchanged += 1
            continue

        last_x = trainer["pos_x"]
        last_y = trainer["pos_y"]
        dir_unchanged = 0

        if opponent_changed():
            return None

    release_all_inputs()
    wait_frames(1)
    press_button("B")
    wait_frames(1)

    return [last_x, last_y]

def follow_path(coords: list, run: bool = True, exit_when_stuck: bool = False):
    direction = None
    
    for x, y in coords:
        logging.info(f"Moving to: {x}, {y}")

        stuck_time = 0

        release_all_inputs()
        while True:
            if run:
                hold_button("B")

            if opponent_changed():
                encounter_pokemon()
                return

            if get_trainer()["pos_x"] == x and get_trainer()["pos_y"] == y:
                release_all_inputs()
                break
            #elif map_data:
            #    # On map change
            #    if get_trainer()["mapBank"] == map_data[0][0] and GetTrainer()["mapId"] == map_data[0][1]:
            #        ReleaseAllInputs()
            #        break

            last_pos = [get_trainer()["pos_x"], get_trainer()["pos_y"]]
            if get_trainer()["pos_x"] == last_pos[0] and get_trainer()["pos_y"] == last_pos[1]:
                stuck_time += 1

                if stuck_time % 180 == 0:
                    logging.info("Bot hasn't moved for a while. Is it stuck?")
                    release_button("B")
                    wait_frames(1)
                    press_button("B")  # Press B occasionally in case there's a menu/dialogue open
                    wait_frames(1)

                    if exit_when_stuck:
                        release_all_inputs()
                        return False
            else:
                stuck_time = 0

            if get_trainer()["pos_x"] > x:
                direction = "Left"
            elif get_trainer()["pos_x"] < x:
                direction = "Right"
            elif get_trainer()["pos_y"] < y:
                direction = "Down"
            elif get_trainer()["pos_y"] > y:
                direction = "Up"

            hold_button(direction)
            wait_frames(1)

        release_all_inputs()
    return True