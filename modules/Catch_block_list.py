import os
import logging
import fastjsonschema

from ruamel.yaml import YAML

from modules.Files import read_file, write_file

log = logging.getLogger(__name__)
yaml = YAML()
yaml.default_flow_style = False

block_schema = {
    "type": "object",
    "properties": {
        "block_list" : {"type": "array"}
    }
}

file = "stats\catch_block_list.yml"

BlockListValidator = fastjsonschema.compile(block_schema)  # Validate the config file to ensure user didn't do a dumb

# Create block list file if doesn't exist
if not os.path.exists(file):
    write_file(file, "block_list: []")
    
def get_block_list():
    catch_block_list_yml = read_file(file)
    if catch_block_list_yml:
        catch_block_list = yaml.load(catch_block_list_yml)
        try:
            if BlockListValidator(catch_block_list):
                return catch_block_list
            return None
        except fastjsonschema.exceptions.JsonSchemaDefinitionException as e:
            log.error(str(e))
            log.error("Block list is invalid!")
            return None