from PIL import Image
import struct
import time

try:
    import mido
    midi_outputs = mido.get_output_names()
    if len(midi_outputs):
    	midi_port = mido.open_output(midi_outputs[0])
    else:
    	midi_port = None
    	print("no midi output found - won't play music")
except ImportError:
	mido = None
	print("mido not found - won't play music")

## PART 1 - "DECRYPT" DATA ##

def xor(data, key):
    return bytearray((
        (data[i] ^ key[i % len(key)]) for i in range(0,len(data))
    ))

data_encrypted = bytearray(open('dump.rom', 'rb').read())
data_temp = xor(data_encrypted,data_encrypted[:16])
for p in range(len(data_encrypted)//16):
	base = 16*p
	if xor(data_encrypted[base:base+16],data_encrypted[base+16:base+16+16]) == b"\x00"*16:
		key = data_encrypted[16*p:16*p+16]
		break
data = xor(data_encrypted, key)
memory = data + bytearray(b"\x00"*(0xFFFF-len(data)))

## PART 2 - RUN CODE ##

def read_short(memory, pos):
	return struct.unpack(">H", memory[pos:pos+2])[0]

def write_short(memory, pos, val):
	memory[pos:pos+2] = struct.pack(">H", val)

def get_instruction(memory, ip):
	data = []
	if memory[ip] & INST_XORV:
		data.append((memory[ip] >> 6) & 1)
		data.append(read_short(memory, ip) & 0b00_111111_11111111)
		return INST_XORV, ip+2, data
	if memory[ip] & INST_XOR == INST_XOR:
		data.append((memory[ip] >> 2) & 0b11)
		data.append(memory[ip] & 0b11)
		return INST_XOR, ip+1, data
	if memory[ip] & INST_RENDER:
		data.append((memory[ip] >> 2) & 0b11)
		return INST_RENDER, ip+1, data
	if memory[ip] & INST_SOUND:
		data.append((memory[ip] >> 2) & 0b11)
		data.append(memory[ip] & 0b11)
		return INST_SOUND, ip+1, data
	return INST_STOP, ip+1, data

# Set up registers
IP = 0
REG_A = 0
REG_B = 0

INST_XORV      = 0b10000000
INST_XORV_MASK = 0b00_111111_11111111
INST_XOR       = 0b00_11_00_00
INST_RENDER    = 0b00_01_00_00
INST_SOUND     = 0b00_10_00_00
INST_STOP      = 0b00_00_00_00

def render_screen(memory,offset):
	image_size = 128
	im = Image.new("1", (image_size, image_size), "black")
	pix = im.load()
	
	for i in range(1024):
		x = i%32
		y = i//32
		b = read_short(memory, offset+i*2)
		for h in range(4):
			for w in range(4):
				pix[(4*x+w,4*y+h)] = b & (1 << (h*4+w))
	
	im.show()


def print_inst(instruction, ip, data, a, b):
	inst_str = {
		INST_XORV: "INST_XORV",
		INST_XOR: "INST_XOR",
		INST_RENDER: "INST_RENDER",
		INST_SOUND: "INST_SOUND",
		INST_STOP: "INST_STOP",
	}[instruction]
	print(f"[IP:{ip:#06x} A:{a:#06x} B:{b:#06x}] {inst_str} {data}")


# Execute code
while True:
	instruction, IP, data = get_instruction(memory, IP)
	print_inst(instruction, IP, data, REG_A, REG_B)

	if instruction == INST_STOP: break
	if instruction == INST_RENDER:
		offset = [REG_A,REG_B][data[0] & 1]
		if data[0] & 0b10:
			offset = read_short(memory, offset)
		render_screen(memory, offset)
	if instruction == INST_SOUND:
		if mido and midi_port:
			note_data = [[REG_A,REG_B][data[0] & 1],[REG_A,REG_B][data[1] & 1]]
			for i in range(2):
				if data[i] & 0b10:
					note_data[i] = read_short(memory, note_data[i])
			midi_port.send(mido.Message('note_on', note=note_data[0]))
			time.sleep(note_data[1]/1000)
			midi_port.send(mido.Message('note_off', note=note_data[0]))
	if instruction == INST_XOR:
		src = [REG_A,REG_B][data[1] & 1]
		if data[1] & 0b10:
			src = read_short(memory, src)
		target = data[0] & 1
		if data[0] & 0b10:
			write_short(memory, REG_B if target else REG_A, src ^ read_short(memory, REG_B if target else REG_A))
		else:
			if target == 0:
				REG_A ^= src
			else:
				REG_B ^= src
	if instruction == INST_XORV:
		if data[0] == 0:
			REG_A ^= data[1]
		else:
			REG_B ^= data[1]
