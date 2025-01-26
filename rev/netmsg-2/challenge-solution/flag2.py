#!/usr/bin/env python3

from flag1 import *
import itertools

# from pcap
interesting_msgs = [
    Msg.deserialize(bytes.fromhex(x))
    for x in (
        "02c8bf0f0093736d32aa748882bf536d9e0b6807184b",
        "02c8bf270094736d1aaa024d1d86931d34f24db7f10b75eedd00e4c4b311dba0c1583ee6e66288809c3fcb0a042f",
        "02c8bf27007b416c42e4117ae95d021d9a35c2dd3df0a8052ae301f43f5d7d986bcdd8232c8d71911c5059ec261e",
    )
]


def factors(n: int) -> tuple[int, int]:
    for i in itertools.chain([2], range(3, int(n**0.5) + 1, 2)):
        if n % i == 0:
            return n // i, i
    raise ValueError(f"{n=} is prime")


def extract_kex() -> None:
    # decrypt kex with static kex key
    kex1 = interesting_msgs[0]
    iv = hashlib.md5(kex1.conn_id.to_bytes(2, "little")).digest()
    kex1_inner = Msg.deserialize(decrypt(kex1.payload, kex_key, iv))

    # extract rsa pubkey
    e = int.from_bytes(kex1_inner.payload[:4], "little")
    n = int.from_bytes(kex1_inner.payload[4:], "little")

    # factor key (32-bit rsa lol lmao)
    p, q = factors(n)
    tot = math.lcm(p - 1, q - 1)
    d = pow(e, -1, tot)

    print(f"extracted rsa keypair: {e=} {n=} {d=}")

    # decrypt and construct session key
    kex2 = interesting_msgs[1]
    kex2_inner = Msg.deserialize(decrypt(kex2.payload, kex_key, iv))

    session_key = b""
    for i in range(8):
        c = int.from_bytes(kex2_inner.payload[i * 4 : i * 4 + 4], "little")
        m = pow(c, d, n)
        session_key += m.to_bytes(2, "little")

    # decrypt username/password message with session key
    user_pwd_msg = interesting_msgs[2]
    user_pwd_inner = Msg.deserialize(decrypt(user_pwd_msg.payload, session_key, iv))
    user = user_pwd_inner.payload[:16].strip(b"\x00").decode()
    passwd = user_pwd_inner.payload[16:].strip(b"\x00").decode()
    print(f"extracted username/password: {user=} {passwd=}")


def flag2(host: str, port: int) -> str:
    x = Conn(host, port)
    x.login("goober_supreme", "1jWXdR0uk62f")

    x.sendwrapped(Msg(6))
    mailbox = x.recvwrapped().payload
    # print(mailbox)

    x.sendwrapped(Msg(9, payload=b"flag"))
    flag = x.recvwrapped().payload.decode()

    x.sendwrapped(Msg(14))
    x.socket.close()

    return flag


def main() -> None:
    extract_kex()
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
    except Exception:
        print(f"usage: {sys.argv[0]} <host> <port>")
        return

    print(flag2(host, port))


if __name__ == "__main__":
    main()
