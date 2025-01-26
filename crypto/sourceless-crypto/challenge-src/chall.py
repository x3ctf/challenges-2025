#!/usr/bin/env python3

import sys

sys.setrecursionlimit(442050)

FLAG = b"MVM{aae30846_08b1_s0urc3less_crypt0_11ef_8010_30894a138cd3}"

nonce = 0


def recr(val, nonce, iter=1):
    if (val * iter) > val << 4:
        return val ^ iter ^ nonce
    return recr(val, nonce, iter=iter + 1)


def encrypt(val: bytes):
    global nonce
    for c in val:
        yield recr(int(c), nonce)
        nonce += 1


EFLAG = bytes(encrypt(FLAG))


def show_flag() -> None:
    print(f"Flag: {EFLAG!r}")


def encrypt_text() -> None:
    text = input("Enter plaintext: ")
    try:
        enc_text = bytes(encrypt(text.encode()))
    except ValueError:
        print("Invalid Input")
        return

    print(f"Encrypted plaintext: {enc_text!r}")


def _exit() -> None:
    sys.exit(0)


def what_are_you_doing() -> None:
    print("What exactly are you trying to do?")


def show_fake_flag() -> None:
    fake_flag = b"mvm{0bv10us_f4k3_fl4g}"
    print(f"Flag: {fake_flag!r}")


def hint() -> None:
    print("Hint: mvm :3")


def not_found(op) -> None:
    print(f"Operation {op!r} not found")


opmap = {
    "1": show_flag,
    "2": encrypt_text,
    "3": _exit,
    "4": what_are_you_doing,
    "5": show_fake_flag,
    "6": hint,
    "flag": show_flag,
    "encrypt": encrypt_text,
    "exit": _exit,
    "hint": what_are_you_doing,
}


def main() -> None:
    print("Welcome to sourceless-crypto, enjoy the pain")
    while True:
        print("1 -> Show Flag\n2 -> Encrypt Plaintext\n3 -> exit")
        operation = input("Operation: ").strip()
        op = opmap.get(operation.strip(), lambda: not_found(operation))

        op()


if __name__ == "__main__":
    main()
