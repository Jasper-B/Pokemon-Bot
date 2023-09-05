import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from threading import Thread
import atexit

from modules.Config import get_config
from modules.Inputs import release_all_inputs, press_button, wait_frames
from modules.Stats import encounter_pokemon, opponent_changed
from modules.General import mode_coords, mode_bonk
from modules.Starters import mode_starters
from modules.mmf.Emu import get_emu
from modules.mmf.Trainer import get_trainer

LogLevel = logging.INFO  # use logging.DEBUG while testing
config = get_config()

# release all inputs on exit
def exit_handler():
    release_all_inputs()
    logging.info("Stopping script and releasing all inputs.")

def main_loop():
    
    release_all_inputs()
    
    while True:
        try:
            if get_trainer() and get_emu(): # Test that emulator information is accesible
                match config["bot_mode"]:
                    case "coords":
                        mode_coords()
                    case "bonk":
                        mode_bonk()
                    case "starters":
                        # run the soft reset function until finished
                        if not mode_starters():
                            break
                    case _:
                        logging.exception("Couldn't interpret bot mode: " + config["bot_mode"])
                        input("Press enter to continue...")
            else:
                release_all_inputs()
                wait_frames(5)
        except Exception as e:
            logging.exception(str(e))
        finally:
            atexit.register(exit_handler)
    
    return False

try:
    # Set up log handler
    LogFormatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(line:%(lineno)d) %(message)s')
    ConsoleFormatter = logging.Formatter('%(asctime)s - %(message)s')
    LogPath = "logs"
    LogFile = f"{LogPath}/debug.log"
    os.makedirs(LogPath, exist_ok=True)  # Create logs directory if not exist

    # Set up log file rotation handler
    LogHandler = RotatingFileHandler(LogFile, maxBytes=20 * 1024 * 1024, backupCount=5)
    LogHandler.setFormatter(LogFormatter)
    LogHandler.setLevel(logging.INFO)

    # Set up console log stream handler
    ConsoleHandler = logging.StreamHandler()
    ConsoleHandler.setFormatter(ConsoleFormatter)
    ConsoleHandler.setLevel(LogLevel)

    # Create logger and attach handlers
    log = logging.getLogger('root')
    log.setLevel(logging.INFO)
    log.addHandler(LogHandler)
    log.addHandler(ConsoleHandler)
except Exception as e:
    print(str(e))
    input("Press enter to continue...")
    os._exit(1)


try:
    # Validate python version
    MinMajorVersion = 3
    MinMinorVersion = 10
    MajorVersion = sys.version_info[0]
    MinorVersion = sys.version_info[1]

    if MajorVersion < MinMajorVersion or MinorVersion < MinMinorVersion:
        log.error(
            f"\n\nPython version is out of date! (Minimum required version for pokebot is "
            f"{MinMajorVersion}.{MinMinorVersion})\nPlease install the latest version at "
            f"https://www.python.org/downloads/\n")
        input("Press enter to continue...")
        os._exit(1)

    log.info(f"Running pokebot on Python {MajorVersion}.{MinorVersion}")
    
    while not get_trainer():
        log.error(
            "\n\nFailed to get trainer data, unable to initialize pokebot!\nPlease confirm that `pokebot.lua` is "
            "running in BizHawk, keep the Lua console open while the bot is active.\nIt can be opened through "
            "'Tools > Lua Console'.\n")
        input("Press enter to try again...")
    config = get_config()  # Load config
    logging.info(f"Mode: {config['bot_mode']}")

    #main = Thread(target=main_loop)
    #main.start()
    while True:
        if not main_loop():
            break

except Exception as e:
    logging.exception(str(e))
    os._exit(1)
