from Crypto.Util.number import long_to_bytes as ltb
from math import gcd
from pwn import *

if args.REMOTE:
	conn = remote('127.0.0.1', 1337)
else:
	conn = process(['python3', 'chall.py'])

conn.recvline()
N = int(conn.recvline().split(b' = ')[1])
e = 0x10001

# This solution script has about a ~0.006% chance of failing
ctr = 0
while True:
	ctr += 1
	conn.recvuntil(b': ')
	conn.sendline(b'2')
	data = int(conn.recvline().split(b' = ')[1])
	enc = int(conn.recvline().split(b' = ')[1])
	correct = pow(data, e, N)
	if enc == correct:
		continue
	p = gcd(enc - correct, N)
	if p != 1 and p != N: # p == N has about a ~0.006% chance of happening
		break

print(f'{ctr} encryption queries')

q = N // p
phi = (p - 1) * (q - 1)
d = pow(e, -1, phi)
conn.recvuntil(b': ')
conn.sendline(b'1')
enc = int(conn.recvline().split(b' = ')[1])
dec = pow(enc, d, N)
conn.sendline(str(dec).encode())

conn.recvuntil(b' = ')
enc = int(conn.recvline())
flag = pow(enc, d, N)
print(ltb(flag))
