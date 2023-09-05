import json
#import numpy
import logging
import fastjsonschema
from datetime import datetime
from modules.Config import get_config
from modules.Files import read_file
from modules.Inputs import wait_frames
from modules.mmf.Common import load_json_mmap
from modules.mmf.Trainer import get_trainer

log = logging.getLogger(__name__)
config = get_config()

ability_list = json.loads(read_file("./modules/data/abilities.json"))
item_list = json.loads(read_file("./modules/data/items.json"))
move_list = json.loads(read_file("./modules/data/moves.json"))

# change to new schema if fully finished
pokemon_schema = {
    "type": "object",
    "properties": {
        "ability": {"type": "number"},
        "nature": {"type": "string"},
        "stats": {"type": "array", "maxItems": 6},
        "EV" : {"type": "array", "maxItems": 6 },
        "IV" : {"type": "array", "maxItems": 6 },
        "xp": {"type": "number"},
        "friendship": {"type": "number"},
        "species_name": {"type": "string"},
        "species_id": {"type": "number"},
        "held_item": {"type": "number"},
        "level": {"type": "number"},
        "max_HP": {"type": "number"},
        "current_HP": {"type": "number"},
        "moves": {"type": "array", "maxItems": 4},
        "OTTID": {"type": "number"},
        "OTSID": {"type": "number"},
        "pid": {"type": "number"},
        "pokerus": {"type": "number"},
        "pp": {"type": "array", "maxItems": 4},
        "shiny_value": {"type": "number"}
    }
}

PokemonValidator = fastjsonschema.compile(pokemon_schema)  # Validate the data from the mmf, sometimes it sends junk

Natures = [
    "Hardy",
    "Lonely",
    "Brave",
    "Adamant",
    "Naughty",
    "Bold",
    "Docile",
    "Relaxed",
    "Impish",
    "Lax",
    "Timid",
    "Hasty",
    "Serious",
    "Jolly",
    "Naive",
    "Modest",
    "Mild",
    "Quiet",
    "Bashful",
    "Rash",
    "Calm",
    "Gentle",
    "Sassy",
    "Careful",
    "Quirky"
]

def enrich_pokemon_data(pokemon: dict):
    """
    Function to add information to the pokemon data extracted from Bizhawk
    :param pokemon: Pokemon data to enrich
    :return: Enriched Pokemon data or None if failed
    """
    try:
        if pokemon["species_name"].isalpha():
            # get the ability from the list
            pokemon["ability"] = ability_list[pokemon["ability"]-1] # minus 1 because of 0-indexing in Python
            # get zero-pad number
            number = pokemon["species_id"]
            pokemon["zero_pad_number"] = f"#{number:03}"
            # get the held-item
            pokemon["held_item"] = "" if pokemon["held_item"] == 0 else item_list[pokemon["held_item"]-1]
            # get IV's individual
            pokemon["hpIV"] = pokemon["IV"][0]
            pokemon["attackIV"] = pokemon["IV"][1]
            pokemon["defenceIV"] = pokemon["IV"][2]
            pokemon["spAttackIV"] = pokemon["IV"][3]
            pokemon["spDefenceIV"] = pokemon["IV"][4]
            pokemon["speedIV"] = pokemon["IV"][5]
            # IV sum
            pokemon["IV_sum"] = (
                pokemon["hpIV"] +
                pokemon["attackIV"] +
                pokemon["defenceIV"] +
                pokemon["spAttackIV"] +
                pokemon["spDefenceIV"] +
                pokemon["speedIV"]
            )
            # get the individual stats
            pokemon["hp"] = pokemon["stats"][0]
            pokemon["attack"] = pokemon["stats"][1]
            pokemon["defence"] = pokemon["stats"][2]
            pokemon["spAttack"] = pokemon["stats"][3]
            pokemon["spDefence"] = pokemon["stats"][4]
            pokemon["speed"] = pokemon["stats"][5]
            # get a shiny boolean, Renegade Platinum is 1:512 for regular Platinum use "< 8"
            pokemon["shiny"] = True if pokemon["shiny_value"] < 128 else False
            # Copy move info out of an array (simplifies CSV logging)
            pokemon["move_1"] = "" if pokemon["moves"][0] == 0 else move_list[pokemon["moves"][0]-1]
            pokemon["move_2"] = "" if pokemon["moves"][1] == 0 else move_list[pokemon["moves"][1]-1]
            pokemon["move_3"] = "" if pokemon["moves"][2] == 0 else move_list[pokemon["moves"][2]-1]
            pokemon["move_4"] = "" if pokemon["moves"][3] == 0 else move_list[pokemon["moves"][3]-1]
            pokemon["move_1_pp"] = pokemon["pp"][0]
            pokemon["move_2_pp"] = pokemon["pp"][1]
            pokemon["move_3_pp"] = pokemon["pp"][2]
            pokemon["move_4_pp"] = pokemon["pp"][3]
            
            # remove unnecessary items
            del pokemon["moves"]
            #del pokemon["shiny_value"]
            del pokemon["stats"]
            del pokemon["IV"]
            del pokemon["pp"]
            
            # Log encounter time
            now = datetime.now()
            year = f"{now.year}"
            month = f"{now.month :02}"
            day = f"{now.day :02}"
            hour = f"{now.hour :02}"
            minute = f"{now.minute :02}"
            second = f"{now.second :02}"
            pokemon["date"] = f"{year}-{month}-{day}"
            pokemon["time"] = f"{hour}:{minute}:{second}"
            
            return pokemon
        else:
            return None
        
    except Exception as e:
        log.debug(str(e))
        return None
        
    

def get_opponent():
    while True:
        try:
            opponent = load_json_mmap(4096, "bizhawk_opponent_data")["opponent"]
            # check if data available
            if opponent == []:
                return False
            if opponent and PokemonValidator(opponent):
                enriched = enrich_pokemon_data(opponent)
                if enriched:
                    return enriched
        except Exception as e:
            log.debug("Failed to GetOpponent(), trying again...")
            log.debug(str(e))


def get_party():
    while True:
        try:
            party_list = []
            party = load_json_mmap(8192, "bizhawk_party_data")["party"]
            # check if data available
            if party == [] or party == [[]]:
                return False
            if party:
                for pokemon in party:
                    if PokemonValidator(pokemon):
                        enriched = enrich_pokemon_data(pokemon)
                        if enriched:
                            party_list.append(enriched)
                            continue
                    else:
                        wait_frames(1)
                        break
                return party_list
        except Exception as e:
            log.debug("Failed to GetParty(), trying again...")
            log.debug(str(e))
            
