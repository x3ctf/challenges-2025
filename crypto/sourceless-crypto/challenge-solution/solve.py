from string import printable

from pwn import remote

r = remote("localhost", 1337)

nonce = 0
r.sendlineafter(b"Operation: ", b"1")
d = r.recvline()
flag = eval(d.replace(b"Flag: ", b""))
dflag = b""

for c in flag:
    dflag += (int(c) ^ nonce).to_bytes(1)
    nonce += 1


r.sendlineafter(b"Operation: ", b"2")
r.sendlineafter(b"plaintext: ", printable.encode())

encrypted_text = r.recvline()
eaaaaa = eval(encrypted_text.replace(b"Encrypted plaintext: ", b""))

eprintable = b""

for c in eaaaaa:
    eprintable += (int(c) ^ (nonce)).to_bytes(1)
    nonce += 1

map = {bytes(e): a for e, a in zip(eprintable, printable)}

for c in dflag:
    print(map.get(bytes(c)), end="")
