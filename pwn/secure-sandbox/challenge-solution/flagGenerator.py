#!/usr/bin/env python3

import io
import qrcode

FLAG = 'MVM{Wh0_N33ds_S3cc0mp_4nyw4y}'

# Slightly inspired by hack.lu CTF 2023 - Soulsplitter

BLOCK_FULL  = chr(9608)
BLOCK_UPPER = chr(9600)
BLOCK_LOWER = chr(9604)
BLOCK_EMPTY = chr(160)

def genCode(data):
    code = qrcode.QRCode(
        border=0,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    )
    code.add_data(data)
    code.make()
    return code

def code_atoms(code):
    size = len(code.modules)
    atoms = []
    for y in range(size):
        for x in range(size):
            atoms.append((x, y, code.modules[y][x]))
    return atoms, size

def atoms_to_text(size, atoms):
    buf = [False] * size**2
    for atom in atoms:
        x, y, is_set = atom
        buf[y * size + x] = is_set
    text = io.StringIO()
    for y in range(0, size, 2):
        for x in range(size):
            a = buf[y * size + x]
            b = buf[(y + 1) * size + x] if (y + 1) * size + x < len(buf) else False
            if a and b:
                text.write(BLOCK_FULL)
            elif a:
                text.write(BLOCK_UPPER)
            elif b:
                text.write(BLOCK_LOWER)
            else:
                text.write(BLOCK_EMPTY)
        text.write('\n')
    return text.getvalue().strip('\n')


code = genCode(FLAG)
atoms, size = code_atoms(code)
qrcodeText = atoms_to_text(size,atoms)

print(qrcodeText)

with open('flag', 'wb') as f:
    f.write(qrcodeText.encode())