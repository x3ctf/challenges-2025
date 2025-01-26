from sage.all import *
from pwn import remote

from json import loads
from server import SAMPLE_MSG, G, bytes_to_long, K_SIZE, REQUIRED_MSG, sha1, n


def recv_json(remote) -> dict:
    return loads(remote.recvline().decode())


rm = remote("localhost", 1337)

rm.sendlineafter(b":", b"sign")
sig = recv_json(rm)

r = ZZ(int(sig["r"], 16))
s = ZZ(int(sig["s"], 16))
z = bytes_to_long(sha1(SAMPLE_MSG.encode()).digest()) % n


def sign_saample_msg(k, d):
    R = k * G
    r = ZZ(R.x()) % n
    s = (k.inverse_mod(n) * (z + r * d)) % n

    return (r, s)


for k in map(ZZ, range(2, 2 ** K_SIZE + 2)):
    try:
        d = (r.inverse_mod(n) * (s * k - z) % n) % n
        if sign_saample_msg(k, d) == (r, s):
            break
    except:
        pass

hash = bytes_to_long(sha1(REQUIRED_MSG.encode()).digest()) % n
R = k * G
r = ZZ(R.x()) % n
s = (k.inverse_mod(n) * (hash + r * d)) % n

rm.sendlineafter(b":", b"mvm")
rm.sendlineafter(b"r:", hex(r).encode())
rm.sendlineafter(b"s:", hex(s).encode())
rm.interactive()
