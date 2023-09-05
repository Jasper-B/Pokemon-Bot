import json
import logging
import os

from modules.data.Game_state import game_state
from modules.Config import get_config
from modules.Files import write_file
from modules.Image import detect_template
from modules.Inputs import button_combo, release_all_inputs, press_button, wait_frames
from modules.Menuing import reset_game, save_game
from modules.Stats import encounter_pokemon
from modules.mmf.Emu import get_emu
from modules.mmf.Pokemon import get_party
from modules.mmf.Trainer import get_trainer

log = logging.getLogger(__name__)
config = get_config()

def mode_starters():
    """
    This mode soft resets until a shiny starter of choice is found.
    Start this script facing the bag of the Professor
    """
    try:
        starter_choice = config["starter"].lower()
        log.debug(f"Starter choice: {starter_choice}")
        
        if starter_choice not in ["turtwig", "chimchar", "piplup"]:
            log.info(f"Unknown starter \"{config['starter']}\". Please edit the value in config.yml and restart the "
                     f"script.")
            input("Press enter to continue...")
            os._exit(1)
        
        # save the game before starting
        log.info("Saving game first")
        save_game()
        # wait after saving before starting script
        wait_frames(180)
            
        log.info(f"Soft resetting for a shiny {starter_choice.capitalize()}...")
        
        while True:
            release_all_inputs()
            
            while get_trainer()["state"] != game_state.OVERWORLD:
                button_combo(["A", 20])
                
            wait_frames(60)
                        
            # press A to open the case
            button_combo(["A", 200, "A", 10])
            
            wait_frames(2)
            
            # choose Turtwig
            if starter_choice == "turtwig":
                while detect_template("choose_text.png"):
                    press_button("A")
                    # confirm choice of turtwig
                    wait_frames(20)
                    if detect_template("turtwig.png"):
                        press_button("A")
                        # wait until back to the overworld
                        wait_frames(100)
                        continue
                    else:
                        print("Not found")
                        return False
                
            
            # choose Chimchar
            if starter_choice == "chimchar":
                while detect_template("choose_text.png"):
                    wait_frames(10)
                    press_button("Right")
                    wait_frames(10)
                    press_button("A")
                    # confirm choice of chimchar
                    wait_frames(20)
                    if detect_template("chimchar.png"):
                        press_button("A")
                        # wait until back to the overworld
                        wait_frames(100)
                        continue
                    else:
                        print("Not found")
                        return False

            # choose Piplup
            if starter_choice == "piplup":
                while detect_template("choose_text.png"):
                    wait_frames(10)
                    press_button("Right")
                    wait_frames(10)
                    press_button("Right")
                    wait_frames(10)
                    press_button("A")
                    # confirm choice of piplup
                    wait_frames(20)
                    if detect_template("piplup.png"):
                        press_button("A")
                        # wait until back to the overworld
                        wait_frames(100)
                        continue
                    else:
                        print("Not found")
                        return False
                        
            # wait for party information
            while not get_party():
                press_button("A")
            
            release_all_inputs()
            
            wait_frames(60)
            
            info = get_party()[0]
            
            # check if shiny
            if info["shiny_value"] < 60000:
                log.info(f"Shiny {starter_choice.capitalize()} found!")
                                
                wait_frames(180)
                
                # get through rival's text
                while get_trainer()["state"] != game_state.MISC_MENU:
                    press_button("A")
                    
                wait_frames(180)
                                
                # battle your rival
                while get_trainer()["state"] == game_state.MISC_MENU:
                    if detect_template("start_menu/battle/fight.png"):
                        # Choose the Normal-type move
                        button_combo(["Down", "A"])
                    press_button("A")
                
                wait_frames(360)
                
                # Mash B until the dialogue ends in your house
                while get_trainer()["state"] != game_state.BAG_MENU:
                    press_button("B")
                    
                wait_frames(360)
                
                # Mash B until the dialogue with Mom ends
                while detect_template("start_menu/text_box.png"):
                    button_combo(["B", 20])
                                
                # save the game
                save_game()
                
                # end the script
                break
            else:
                # soft-reset if not shiny
                name = info["species_name"]
                sum = info["IV_sum"]
                sv = info["shiny_value"]
                log.info(
                    f"Found a {name} with an IV sum of {sum} and a shiny value of {sv}."
                    )
                log.info("Not shiny, soft-resetting...")
                
                reset_game()
                
                # mash A until the continue screen is detected
                while not detect_template("start_menu/continue_game.png"):
                    button_combo(["A", 10])
                                
                press_button("A")
                wait_frames(60)
                continue
        
        return False

    except Exception as e:
        log.exception(str(e))