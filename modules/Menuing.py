import json
import logging
import os

from modules.Config import get_config
from modules.Catch_block_list import get_block_list
from modules.data.Game_state import game_state
from modules.Files import read_file
from modules.Image import detect_template
from modules.Inputs import button_combo, hold_button, release_all_inputs, release_button, press_button, wait_frames
from modules.mmf.Pokemon import get_opponent
from modules.mmf.Trainer import get_trainer

log = logging.getLogger(__name__)
config = get_config()

no_sleep_abilities = ["Shed Skin", "Insomnia", "Vital Spirit"]
pickup_pokemon = ["Meowth", "Aipom", "Phanpy", "Teddiursa", "Zigzagoon", "Linoone"]

#type_list = json.loads(read_file("./modules/data/types.json"))

def start_menu(entry: str):
    """
    Function to open any start menu item - presses START, finds the menu entry and opens it
    :param entry: String of menu option to select
    :return: Boolean value of whether menu item was selected
    """
    entry = entry.lower()
    
    if entry not in ["bag", "bot", "exit", "options", "pokedex", "pokemon", "save"]:
        return False
    
    log.info(f"Opening start menu entry: {entry}")
    filename = f"start_menu/{entry}.png"
    
    press_button("B")
    release_all_inputs()
    
    while not detect_template("start_menu/start_menu.png"):
        button_combo(["B", "X"])
        
        for _ in range(10):
            if detect_template("start_menu/start_menu.png"):
                break
            wait_frames(5)
            
    wait_frames(5)
    
    while not detect_template(filename): # Find menu entry
        button_combo(["Down", 10])
        
    while detect_template(filename): # Press menu entry
        button_combo(["A", 10])
    return True

def bag_menu(category: str, item: str):
    """
    Function to find an item in the bag in the overworld
    :param category: String value of bag section selection
    :param item: String value of item
    :return: Boolean value of whether item was found
    """
    if category not in ["items", "medicine", "poke_balls", "tm_hm", "berries", "mail", "battle_items", "key_items"]:
        return False
    
    log.info(f"Scrolling to bag category: {category}...")
    
    while not detect_template(f"start_menu/bag/{category.lower()}.png"):
        button_combo(["Right", 25]) # Press right until the correct category is selected
        
    wait_frames(60) # wait for animations
    
    log.info(f"Scanning for item: {item}...")
    
    i = 0
    while not detect_template(f"start_menu/bag/items/{item.lower()}.png") and i < 50:
        if i < 25:
            button_combo(["Down", 15])
        else:
            button_combo(["Up", 15])
        i += 1
    
    wait_frames(60) # wait for animations
    
    if detect_template(f"start_menu/bag/items/{item.lower()}.png"):
        log.info(f"Using item: {item}...")
        while get_trainer()["state"] == 17:
            button_combo(["A", 1])
        return True
    return False

def battle_menu(category: str):
    """
    Function to find an item in the bag during battle
    :param category: String value of bag section selection
    :param item: String value of item
    :return: Boolean value of whether item was found
    """
    if category not in ["bag", "fight", "run", "switch"]:
        return False
    
    if get_trainer()["state"] == game_state.OVERWORLD:
        return False
    
    while not detect_template(f"start_menu/battle/fight.png"):
        press_button("B")
     
    if not detect_template(f"start_menu/battle/fight1.png") or detect_template(f"start_menu/battle/fight2.png") or detect_template(f"start_menu/battle/fight3.png"):
        button_combo(["B", 10, "Right", 2, "Right", 2, "Up", 2]) # this makes sure it always starts at fight

    if category == "fight":
        press_button("A")
        return True
    elif category == "bag":
        button_combo(["Left", 2, "A"])
        return True
    elif category == "switch":
        button_combo(["Right", 2, "A"])
        return True
    elif category == "run":
        button_combo(["Right", 2, "Left", 2, "A"])
        return True
    
def save_game():
    """Function to save the game via the save option in the start menu"""
    try:
        log.info("Saving the game...")

        i = 0
        start_menu("save")
        while i < 2:
            while not detect_template("start_menu/save/yes.png"):
                wait_frames(10)
            while detect_template("start_menu/save/yes.png"):
                button_combo(["A", 30])
                i += 1
        # Wait for game to save
        while not detect_template("start_menu/save/save_finished.png"):
            wait_frames(10)
        wait_frames(60)
        press_button("H")  # Flush Bizhawk SaveRAM to disk
    except Exception as e:
        log.exception(str(e))

def reset_game():
    """Function to soft reset the game"""
    log.info("Resetting...")
    hold_button("Start")
    hold_button("Select")
    hold_button("L")
    hold_button("R")
    wait_frames(5)
    release_all_inputs()

def catch_pokemon():
    """
    Function to catch pokemon
    :return: Boolean value of whether Pokemon was successfully captured
    """
    opponent = get_opponent()
    try:
        if not detect_template(f"start_menu/battle/fight1.png") or detect_template(f"start_menu/battle/fight2.png") or detect_template(f"start_menu/battle/fight3.png"):
            button_combo(["B", 30, "Right", 2, "Right", 2, "Up", 2]) # this makes sure it always starts at fight
            
        if config["manual_catch"]:
            input(
                "Pausing bot for manual catch (don't forget to pause pokebot.lua script so you can provide inputs). "
                "Press Enter to continue...")
            return True
        else:
            log.info("Attempting to catch Pokemon...")
        
        # ADD SPORE ABILITY
        #if config["use_spore"]:  # Use Spore to put opponent to sleep to make catches much easier
        
        while True:
            while not detect_template(f"start_menu/battle/fight.png"):
                press_button("B")
    
            battle_menu("bag") # open the bag

            wait_frames(30)
        
            # move to the pokeballs section
            if not detect_template(f"start_menu/battle/bag_open1.png") or detect_template(f"start_menu/battle/bag_open2.png") or detect_template(f"start_menu/battle/bag_open3.png"):
                button_combo(["Left", 2, "Up", 2, "Right", 2, "A"]) # this makes sure it always goes to the pokeball section
    
            wait_frames(30)
    
            # ADD POKEBALL PRIORITY
            if not detect_template(f"start_menu/battle/pokeballs/pokeball1.png") or detect_template(f"start_menu/battle/pokeballs/pokeball2.png") or detect_template(f"start_menu/battle/pokeballs/pokeball3.png"):
                button_combo(["Left", 2, "A", 30, "A", 30])
    
            while True:
                press_button("B")
                if detect_template(f"start_menu/battle/fight.png"):
                    print("Fight menu")
                    break
                elif detect_template(f"start_menu/battle/gotcha.png"):
                    print("Caught")
                    
                    release_all_inputs()
                    log.info("Pokemon caught!")
                    
                    wait_frames(500)
                    
                    # press A if new pokedex entry
                    if detect_template(f"start_menu/battle/new_pokedex1.png") or detect_template(f"start_menu/battle/new_pokedex2.png"):
                        print("Detected pokedex")
                        while detect_template(f"start_menu/battle/new_pokedex1.png") or detect_template(f"start_menu/battle/new_pokedex2.png"):
                            press_button("A")
                    else:
                        print("not detected pokedex")
                    
                    print("Continuing")
                    
                    # press B until back to overworld
                    while get_trainer()["state"] != game_state.OVERWORLD:
                        press_button("B")
                    
                    wait_frames(120)
                    
                    if config["save_game_after_catch"]:
                        save_game()
                    
                    return True
            
    except Exception as e:
        log.exception(str(e))
        return False

def flee_battle():
    """Function to run from wild pokemon"""
    try:
        log.info("Running from battle...")
        battle_menu("run")
        wait_frames(200)
    except Exception as e:
        log.exception(str(e))
    
            