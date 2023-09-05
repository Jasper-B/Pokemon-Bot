-- remove depraciation warnings
--bit = (require "migration_helpers").EmuHawk_pre_2_9_bit();

-- set to the main RAM memory
memory.usememorydomain("Main RAM")

-- open this file with pokemon names
dofile "data/pokemondata.lua" -- Pokemon names, abilities, moves

-- Allocate memory mapped file sizes
comm.mmfWrite("bizhawk_screenshot", string.rep("\x00", 24576))
comm.mmfSetFilename("bizhawk_screenshot")
comm.mmfScreenshot()

comm.mmfWrite("bizhawk_emu_info", string.rep("\x00", 4096))
comm.mmfWrite("bizhawk_location", string.rep("\x00", 4096))

-- Functions for reading in the RAM (from https://github.com/40Cakes/pokebot-bizhawk/blob/main/data/lua/Memory.lua)
Memory = {}

function Memory.read(addr, size)
	if size == 1 then
		return memory.read_u8(addr,mem)
	elseif size == 2 then
		return memory.read_u16_le(addr,mem)
	elseif size == 3 then
		return memory.read_u24_le(addr,mem)
	else
		return memory.read_u32_le(addr,mem)
	end 
end

function Memory.readdword(addr)
	return Memory.read(addr, 4)
end

function Memory.readword(addr)
	return Memory.read(addr, 2)
end

function Memory.readbyte(addr)
	return Memory.read(addr, 1)
end

function getbits(a,b,d) -- Get bits (kinda obvious right ?)
	return (a >> b) % (1 << d)
end

function mult32(a,b) -- 32 bits multiplication
	local c = a >> 16
	local d = a % 0x10000
	local e = b >> 16
	local f = b % 0x10000
	local g = (c*f+d*e) % 0x10000
	local h = d*f
	local i = g*0x10000+h
	return i
end

function gettop(a) -- Rshift for data decryption
	return(a >> 16)
end

-- Compares pid and checksum with current pid and checksum
--function check_last(pid,checksum) 
--	local lastpid = pid
--	local lastchecksum = checksum
--	local currentchecksum
--	local currentpid
--	
--	
--	currentpid = Memory.readdword(start)
--	currentchecksum = Memory.readword(start + 6)
--	
--	if lastpid == currentpid and lastchecksum == currentchecksum then
--		return 1
--	else
--		return 0
--		
--	end
--end

-- Get Pokemon stats
function get_pokemon_info(address)
	if address ~= nil then
		local pokemon={}
		local decrypted={}
		-- bit functions are depracated in Bizhawk, source of a lot of unseen errors
		--local bnd,br,bxr=bit.band,bit.bor,bit.bxor
		--local rshift, lshift=bit.rshift, bit.lshift
		local prng

		pokemon["addr"] = address
		-- get the PID, checksum, and use this to calculate the shift value
		pokemon["pid"] = Memory.readdword(pokemon["addr"])

		-- if the pid value is really low, there is no opponent data
		if Memory.readdword(address) < 0x10000001 then
			return {}
		end

		-- get p1 and p2 for the shiny value calculation
		pokemon["p1"] = Memory.readword(pokemon["addr"]+2)
		pokemon["p2"] = Memory.readword(pokemon["addr"])
		pokemon["checksum"] = Memory.readword(pokemon["addr"]+6)
		pokemon["shift"] = ((pokemon["pid"] & 0x3E000) >> 0xD) % 24 --(rshift((bnd(pokemon["pid"],0x3E000)),0xD)) % 24
		
		nature_location = pokemon["pid"] % 25 + 1
		pokemon["nature"] = table["nature"][nature_location]

		-- Offsets
		offset={}
		offset["A"] = (table["growth"][pokemon["shift"]+1]-1) * 32
		offset["B"] = (table["attack"][pokemon["shift"]+1]-2) * 32
		offset["C"] = (table["effort"][pokemon["shift"]+1]-3) * 32
		offset["D"] = (table["misc"][pokemon["shift"]+1]-4) * 32

		-- PRNG is seeded with checksum then it has to be calculated every 2 bytes word
		prng = pokemon["checksum"]
			
		-- Decrypting the memory into a table
		for i=0x08, 0x86, 2 do
			prng = mult32(prng,0x41C64E6D) + 0x6073
			-- Big bug in the depracation of bxr, should finally work now
			decrypted[i]= (prng >> 16) ~ Memory.readword(pokemon["addr"]+i) --bxr(Memory.readword(pokemon["addr"]+i), )
			
			-- There was a bug that took hours to fix, but the problem was that the
			-- decrypted bytes could go above the max of 65535 in this version and
			-- in the Desmume version this was then automatically changed to zero.
			-- with the below change this is finally fixed!
			if decrypted[i] > 65535 then
				decrypted[i] = decrypted[i] - 65536
			end
		end

		-- Battle Stats
		-- Seed is PID (and the bytes aren't shuffled)
		prng = pokemon["pid"]
		-- Then we keep decrypting the memory the same way
		for i=0x88, 0xEA, 2 do
			prng = mult32(prng,0x41C64E6D) + 0x6073
			-- Big bug in the depracation of bxr, should finally work now
			decrypted[i]= (prng >> 16) ~ Memory.readword(pokemon["addr"]+i) --bxr(Memory.readword(pokemon["addr"]+i), gettop(prng))

			-- THere was a bug that took hours to fix, but the problem was that the
			-- decrypted bytes could go above the max of 65535 in this version and
			-- in the Desmume version this was then automatically changed to zero.
			-- with the below change this is finally fixed!
			if decrypted[i] > 65535 then
				decrypted[i] = decrypted[i] - 65536
			end
		end
		
		-- Use decrypted data to get info on wild encounter
		-- Block A
		pokemon["species_id"] = decrypted[0x08+offset["A"]]
		pokemon["species_name"] = table["pokemon"][decrypted[0x08+offset["A"]]]
		pokemon["held_item"] = decrypted[0x0A+offset["A"]]
		pokemon["OTTID"] = decrypted[0x0C+offset["A"]]
		pokemon["OTSID"] = decrypted[0x0E+offset["A"]]
		pokemon["xp"] = decrypted[0x10+offset["A"]]
		pokemon["friendship"] = getbits(decrypted[0x14+offset["A"]],0,8)
		pokemon["ability"] = getbits(decrypted[0x14+offset["A"]],8,8)
		--pokemon["markings"] = decrypted[0x16+offset["A"]]
		--pokemon["language"] = decrypted[0x17+offset["A"]]
		pokemon["EV"]={getbits(decrypted[0x18+offset["A"]],0,8),getbits(decrypted[0x18+offset["A"]],8,8),getbits(decrypted[0x1A+offset["A"]],0,8),getbits(decrypted[0x1C+offset["A"]],0,8),getbits(decrypted[0x1C+offset["A"]],8,8),getbits(decrypted[0x1A+offset["A"]],8,8)}
		--pokemon["contest"]={getbits(decrypted[0x1E+offset["A"]],0,8),getbits(decrypted[0x1E+offset["A"]],8,8),getbits(decrypted[0x20+offset["A"]],0,8),getbits(decrypted[0x20+offset["A"]],8,8),getbits(decrypted[0x22+offset["A"]],0,8),getbits(decrypted[0x22+offset["A"]],8,8)}
		--pokemon["ribbon"]={decrypted[0x24+offset["A"]],decrypted[0x26+offset["A"]]}

		-- Block B
		pokemon["moves"]={decrypted[0x28+offset["B"]],decrypted[0x2A+offset["B"]],decrypted[0x2C+offset["B"]],decrypted[0x2E+offset["B"]]}
		pokemon["pp"]={getbits(decrypted[0x30+offset["B"]],0,8),getbits(decrypted[0x30+offset["B"]],8,8),getbits(decrypted[0x32+offset["B"]],0,8),getbits(decrypted[0x32+offset["B"]],8,8)}
		pokemon["ivs"]=decrypted[0x38+offset["B"]]  + (decrypted[0x3A+offset["B"]] << 16) --lshift(decrypted[0x3A+offset["B"]],16)
		pokemon["IV"]={getbits(pokemon["ivs"],0,5),getbits(pokemon["ivs"],5,5),getbits(pokemon["ivs"],10,5),getbits(pokemon["ivs"],20,5),getbits(pokemon["ivs"],25,5),getbits(pokemon["ivs"],15,5)}
		pokemon["stats"]={decrypted[0x90],decrypted[0x92],decrypted[0x94],decrypted[0x98],decrypted[0x9A],decrypted[0x96]}
		pokemon["level"] = decrypted[0x8C]
		pokemon["pokerus"]=getbits(decrypted[0x82],0,8)
		pokemon["current_HP"]=decrypted[0x8E]
		pokemon["max_HP"]=decrypted[0x90]
		--pokemon["hiddenpower"]={}
		--pokemon["hiddenpower"]["type"]=math.floor(((pokemon["iv"][1]%2 + 2*(pokemon["iv"][2]%2) + 4*(pokemon["iv"][3]%2) + 8*(pokemon["iv"][6]%2) + 16*(pokemon["iv"][4]%2) + 32*(pokemon["iv"][5]%2))*15)/63)
		--pokemon["hiddenpower"]["base"]=math.floor((( getbits(pokemon["iv"][1],1,1) + 2*getbits(pokemon["iv"][2],1,1) + 4*getbits(pokemon["iv"][3],1,1) + 8*getbits(pokemon["iv"][6],1,1) + 16*getbits(pokemon["iv"][4],1,1) + 32*getbits(pokemon["iv"][5],1,1))*40)/63 + 30)
		
		-- calculate the shiny value
		pokemon["shiny_value"] = (pokemon["OTTID"] ~ pokemon["OTSID"] ~ pokemon["p1"] ~ pokemon["p2"])

		pokemon["ivs"] = nil
		pokemon["p1"] = nil
		pokemon["p2"] = nil
		pokemon["addr"] = nil
		pokemon["checksum"] = nil
		pokemon["shift"] = nil

		lastpid = pokemon["pid"]
		return pokemon
	end
end

-- Function to get info about the trainer
function get_trainer(address)
	local trainer = {}

	-- all RAM locations are relative to the TID location
	trainer["tid"] = Memory.readword(address)
	trainer["sid"] = Memory.readword(address+2)
	trainer["pos_x"] = Memory.readword(address+145492)
	trainer["pos_y"] = Memory.readword(address+145488)
	trainer["state"] = Memory.readbyte(address+394646)
	--trainer["bag_state"] = Memory.readdword(0x2d3ec8)

	return trainer
end


-- Function to get data of all Pokemon in the player's party
function get_party(address)
	if address ~= nil then
		local party = {}
		local party_start = address-178088
		local party_count = Memory.readbyte(address-178092)

		-- party is a maximum of 6 Pokemon, otherwise the calculations would be huge
		-- because after soft-resetting this can go to >80!
		--if party_count > 6 then
		--	party_count = 1
		--end
	
		for i = 1, party_count do
			party[i] = get_pokemon_info(party_start)
			party_start = party_start + 236 -- Pokemon data structure is 236 bytes
		end
	
		return party
	end
end