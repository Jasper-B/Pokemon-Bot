-- Renegade Platinum script
-- by Jasper Bannenberg
-- v0.1 6-june-2023

-- adapted from https://github.com/yling/yPokeStats

dofile "data/Renegade_platinum_memory.lua" -- Functions and Pokemon table generation
dofile "data/tables.lua" -- Tables with games data, and various data - including names

print("Welcome to Pokémon Renegade Platinum")

-- These packages are required
local utils = require("utils")
json = require "json"

local utils = {}

function utils.translatePath(path)
	local separator = package.config:sub(1, 1)
	local pathTranslated = string.gsub(path, "\\", separator)
	return pathTranslated == nil and path or pathTranslated
end

enable_input = true -- Toggle inputs to the emulator, useful for testing
write_files = true -- Toggle output of data to files (press L+R in emulator to save files to testing/ folder)

-- Release all keys after starting script
if enable_input then
	input = joypad.get()
	input["A"], input["B"], input["L"], input["R"], input["Up"], input["Down"], input["Left"], input["Right"], input["Select"], input["Start"], input["Screenshot"], input["SaveRAM"] = false, false, false, false, false, false, false, false, false, false, false, false
	joypad.set(input)
end

-- Allocate memory mapped file sizes
comm.mmfWrite("bizhawk_screenshot", string.rep("\x00", 24576))
comm.mmfSetFilename("bizhawk_screenshot")
comm.mmfScreenshot()

comm.mmfWrite("bizhawk_press_input", string.rep("\x00", 4096))
comm.mmfWrite("bizhawk_hold_input", string.rep("\x00", 4096))
comm.mmfWrite("bizhawk_emu_info", string.rep("\x00", 4096))
comm.mmfWrite("bizhawk_trainer_data", string.rep("\x00", 4096))
comm.mmfWrite("bizhawk_opponent_data", string.rep("\x00", 4096))
comm.mmfWrite("bizhawk_party_data", string.rep("\x00", 8192))

input_list = {}
for i = 0, 100 do --101 entries, the final entry is for the index.
	input_list[i] = string.byte("a")
end

-- Create memory mapped input files for Python script to write to
comm.mmfWrite("bizhawk_hold_input", json.encode(input) .. "\x00")
comm.mmfWrite("bizhawk_input_list", string.rep("\x00", 4096))

comm.mmfWriteBytes("bizhawk_input_list", input_list)


last_posY = 0
last_posX = 0
last_state = 0
last_mapBank = 0
last_mapId = 0


-- This is the start location of the info in the main RAM
-- I since found out that the location in the RAM changes upon resetting.
-- Therefore, I will put in the trained ID and it can then search for the
-- correct starting locations
local TID = 50338
local start = 0

function ram_offset(tid)
	local offset = {}

	for i = 0x27e000, 0x27e800, 4 do
		if Memory.readword(i) == tid then
			offset["tid_location"] = i
			offset["start_location"] = i + 178128 -- this is the difference between the TID and the startlocation
			break
		end
	end

	return offset
end

--local party_start = 0x27e24c

-- Main function to get the location, opponent info and party info
function main()
	-- first get the start location based on the TID
	if start == 0 then
		offset = ram_offset(TID)
	end

	-- check if the RAM locations have shifted
	if Memory.readword(offset["tid_location"]) ~= TID then
		offset = ram_offset(TID)
	end

	-- only do calculations when there is a start location
	if offset["start_location"] or offset["tid_location"] ~= nil then
		-- get the trainer info every frame
    	trainer = get_trainer(offset["tid_location"])
    	-- get the opponent pokemon information
		opponent = get_pokemon_info(offset["start_location"])
		-- get the party pokemon information
    	party = get_party(offset["start_location"])

		comm.mmfWrite("bizhawk_trainer_data", json.encode({["trainer"] = trainer}) .. "\x00")
		comm.mmfWrite("bizhawk_opponent_data", json.encode({["opponent"] = opponent}) .. "\x00")
		comm.mmfWrite("bizhawk_party_data", json.encode({["party"] = party}) .. "\x00")
	end

	

    if write_files then
		check_input = joypad.get()
		if check_input["L"] and check_input["R"] then
			trainer_data_file = io.open(
				utils.translatePath("testing\\trainer_data.json"), "w"
			)
			trainer_data_file:write(json.encode({["trainer"] = trainer}))
			trainer_data_file:close()
			
			party_data_file = io.open(
				utils.translatePath("testing\\party_data.json"), "w"
			)
			party_data_file:write(json.encode({["party"] = party}))
			party_data_file:close()

			opponent_data_file = io.open(
				utils.translatePath("testing\\opponent_data.json"), "w"
			)
			opponent_data_file:write(json.encode({["opponent"] = opponent}))
			opponent_data_file:close()
		end
	end
	
	comm.mmfScreenshot()

end


g_current_index = 1 --Keep track of where Lua is in it's traversal of the input list
function traverseNewInputs()
	local pcall_result, list_of_inputs = pcall(comm.mmfRead,"bizhawk_input_list", 4096)
	if pcall_result == false then
		gui.addmessage("pcall fail list")
		return false	
	end
	local current_index = g_current_index
	python_current_index = list_of_inputs:byte(101)
	if current_index ~= python_current_index then
		while (current_index) ~= python_current_index do
			current_index = current_index + 1
			if current_index > 100 then
				current_index = 1
			end
			button = utf8.char(list_of_inputs:byte(current_index))
			if button == "l" then
				button = "Left"
			end
			if button == "r" then
				button = "Right"
			end
			if button == "u" then
				button = "Up"
			end
			if button == "d" then	
				button = "Down"
			end
			if button == "s" then
				button = "Select"
			end
			if button == "S" then
				button = "Start"
			end
			input[button] = true
			if button == "A" then
				input["B"] = false --If there are any new "A" presses after "B" in the list, discard the "B" presses before it
			end
			if button == "H" then
				client.saveram()
				console.log("SaveRAM flushed!")
			end
		end
		
	end
	g_current_index = current_index
	if enable_input then
		joypad.set(input)
	end
end

function handleHeldButtons()
	
	local pcall_result, hold_result = pcall(json.decode, comm.mmfRead("bizhawk_hold_input", 4096))
	if pcall_result then
		held_buttons = hold_result
	end
	for button, button_is_held in pairs (held_buttons) do
		if button_is_held then
			input[button] = true
		else
			; --Don't assign them false, this function is called after the presses and would overwrite them to false
		end
	end
	--if (last_state ~= trainer.state) then
	--	last_state = trainer.state
	--end

	if enable_input then
		joypad.set(input)
	end

end

-- Function to get data related to the emulator itself
function get_emu()
	local emu_data = {
		frameCount = emu.framecount(),
		emuFPS = client.get_approx_framerate(),
		rngState = memory.read_u16_le(0x021BFB14, "ARM9 System Bus")
	}
	
	return emu_data
end



-- main loop
main()
NUM_OF_FRAMES_PER_PRESS = 5

while true do
    emu_data = get_emu()

    if emu_data.frameCount % NUM_OF_FRAMES_PER_PRESS == 0 then --Every n frame will skip the presses, so you can spam inputs in Python and them not get held, they won't be eaten, just deferred a frame. 
		for button, buttons in pairs (input) do
			input[button] = false 
			if enable_input then
				joypad.set(input)
			end
		end
	else
		traverseNewInputs()

	end
	handleHeldButtons()

    main()
        
	-- Save screenshot and other data to memory mapped files, as FPS is higher, reduce the number of reads and writes to memory
	comm.mmfWrite("bizhawk_emu_data", json.encode({["emu"] = emu_data}) .. "\x00")
    fps = emu_data.emuFPS

    if fps > 120 and fps <= 240  then -- Copy screenshot to memory every nth frame if running at higher than 1x to reduce memory writes
		if (emu_data.frameCount % 2 == 0) then
			main()
		end
	elseif fps > 240 and fps <= 480 then 
		if (emu_data.frameCount % 3 == 0) then
			main()
		end	
	elseif fps > 480 then 
		if (emu_data.frameCount % 4 == 0) then
			main()
		end	
	else
		main()
	end

	-- Frame advance
	emu.frameadvance()
end

