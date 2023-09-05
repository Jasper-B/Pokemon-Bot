import os
import json
import logging

from modules.Config import get_config
from modules.data.Game_state import game_state
from modules.Files import read_file, write_file
from modules.Inputs import release_all_inputs, press_button, wait_frames
from modules.mmf.Pokemon import get_opponent
from modules.mmf.Trainer import get_trainer
from modules.Catch_block_list import get_block_list
from modules.Menuing import flee_battle, catch_pokemon

log = logging.getLogger(__name__)
config = get_config()

last_opponent_personality = 0

def opponent_changed():
    """
    This function checks if there is a different opponent since last check, indicating the game state is probably
    now in a battle
    :return: Boolean value of whether in a battle
    """
    global last_opponent_personality
    try:
        if get_trainer()["state"] == game_state.OVERWORLD:
            return False
        
        opponent = get_opponent()
        if opponent:
            new_pid = opponent['pid']
            log.debug(
                f"Checking if opponent's PID has changed... (if {last_opponent_personality} != {new_pid})")
            if last_opponent_personality != new_pid:
                log.info(
                    f"Opponent has changed! Previous PID: {f'{last_opponent_personality:0x}'}, New PID: {f'{new_pid:0x}'}")
                last_opponent_personality = new_pid
                return True
            return False
    except Exception as e:
        log.exception(str(e))
        return False
    
def encounter_pokemon(starter: bool = False):
    """
    New Pokemon encountered, record stats + decide whether to catch/battle/flee
    :param starter: Boolean value of whether in starter mode
    :return: Boolean value of whether in battle
    """
    legendary_hunt = config["bot_mode"] in ["manual", "rayquaza", "kyogre", "groudon", "southern island", "regis",
                                            "deoxys resets", "deoxys runaways", "mew"]
    
    log.info("Identifying Pokemon...")
    release_all_inputs()
    
    if starter:
        wait_frames(30)
    else:
        for _ in range(250):
            if get_trainer()["state"] in [3, 255]:
                break
    
    if get_trainer()["state"] == game_state.OVERWORLD:
        return False
    
    # implement get_party 
    pokemon = get_opponent()
    #log_encounter(pokemon)
    
    replace_battler = False
    
    # implement that shiny-values below threshold are Boolean shiny or not 
    # (below 128 for Renegade platinum, below 8 for official version)
    if pokemon["shiny"]:
        if not starter and not legendary_hunt and config["catch_shinies"]:
            blocked = get_block_list()
            opponent = get_opponent()
            if opponent["speciesname"] in blocked["block_list"]:
                log.info("---- Pokemon is in list of non-captures. Fleeing battle ----")
                flee_battle()
            else:
                catch_pokemon()
        elif legendary_hunt:
            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can "
                  "provide inputs). Press Enter to continue...")
        return True
    else:
        if config["bot_mode"] == "manual":
            while get_trainer()["state"] != game_state.OVERWORLD:
                wait_frames(100)
        elif starter:
            return False
        
        # ADD CATCH CONFIG
        #if custom_catch_config(pokemon):
        #    catch_pokemon()
        
        if not legendary_hunt:
            # ADD BATTLE MECHANIC
            #if config["battle_others"]
            flee_battle()