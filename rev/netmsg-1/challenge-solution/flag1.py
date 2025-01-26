#!/usr/bin/env python3

import socket
import struct
import math
import sys
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto.Util.number import getPrime
from dataclasses import dataclass
import hashlib


def crc16(data: bytes, poly: int = 0x8408) -> int:
    """
    CRC-16-CCITT Algorithm
    """
    data = bytearray(data)
    crc = 0xFFFF
    for b in data:
        cur_byte = b & 0xFF
        for _ in range(8):
            if (crc & 1) ^ (cur_byte & 1):
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
            cur_byte >>= 1
    crc = ~crc & 0xFFFF

    return crc


"""
      puVar4[0] = 0x11;
      puVar4[1] = 0x4a;
      puVar4[2] = 0x5b;
      puVar4[3] = 0xc7;
      puVar4[4] = 0xc;
      puVar4[5] = 0xac;
      puVar4[6] = 0xd5;
      puVar4[7] = 0x8c;
      puVar4[8] = 0xa5;
      puVar4[9] = 0x4d;
      puVar4[10] = 0x70;
      puVar4[0xb] = 0xc4;
      puVar4[0xc] = 0x79;
      puVar4[0xd] = 0x7a;
      puVar4[0xe] = 0xed;
      puVar4[0xf] = 0x13;
"""

kex_key = bytes.fromhex("114a5bc70cacd58ca54d70c4797aed13")


def encrypt(b: bytes, key: bytes, iv: bytes) -> bytes:
    counter = Counter.new(8, prefix=iv[:15], initial_value=iv[15])
    cipher = AES.new(key, AES.MODE_CTR, counter=counter)

    return cipher.encrypt(b)


def decrypt(b: bytes, key: bytes, iv: bytes) -> bytes:
    return encrypt(b, key, iv)


def generate_rsa() -> tuple[int, int, int]:
    e = 65537
    p = getPrime(16)
    q = getPrime(16)
    n = p * q
    tot = math.lcm(p - 1, q - 1)
    d = pow(e, -1, tot)

    return e, d, n


@dataclass
class Msg:
    msg_type: int = 0
    conn_id: int = 0
    # msg_len: int
    payload: bytes = b""
    # crc: int

    @staticmethod
    def from_socket(s: socket.socket) -> "Msg":
        t_id_len = s.recv(5)
        _msg_type, _conn_id, msg_len = struct.unpack("<BHH", t_id_len)
        payload_crc = s.recv(msg_len + 2)

        return Msg.deserialize(t_id_len + payload_crc)

    @staticmethod
    def deserialize(b: bytes) -> "Msg":
        msg_type, conn_id, msg_len = struct.unpack("<BHH", b[:5])
        payload = b[5 : 5 + msg_len]
        crc_b = b[5 + msg_len :]
        if not (len(payload) == msg_len and len(crc_b) == 2):
            raise Exception("invalid payload len")

        msg_crc = int.from_bytes(crc_b, "little")
        calc_crc = crc16(b[:-2])
        if msg_crc != calc_crc:
            raise Exception("crc mismatch in msg")

        return Msg(msg_type, conn_id, payload)

    def serialize(self) -> bytes:
        encoded = struct.pack("<BHH", self.msg_type, self.conn_id, len(self.payload))
        encoded += self.payload
        encoded += crc16(encoded).to_bytes(2, "little")

        return encoded

    def to_socket(self, s: socket.socket) -> None:
        encoded = self.serialize()

        s.send(encoded)

    def to_wrapped(self, key: bytes, iv: bytes) -> "Msg":
        serialized = self.serialize()
        payload = encrypt(serialized, key, iv)
        return Msg(2, self.conn_id, payload)

    def from_wrapped(self, key: bytes, iv: bytes) -> "Msg":
        serialized = decrypt(self.payload, key, iv)
        return Msg.deserialize(serialized)


class Conn:
    def __init__(self, host: str, port: int) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn_id = 0
        self.crypto_key = kex_key

        self._connect(host, port)

    def _connect(self, host: str, port: int) -> None:
        self.socket.connect((host, port))

        # hello
        self.sendmsg(Msg(1))
        msg = self.recvmsg()
        if msg.msg_type != 1:
            raise Exception("expected hello back")
        self.conn_id = msg.conn_id

        e, d, n = generate_rsa()
        self.sendwrapped(Msg(3, payload=struct.pack("<LL", e, n)))
        aes_key_msg = self.recvwrapped()

        session_aes_key = b""

        for i in range(8):
            chunk = aes_key_msg.payload[i * 4 : i * 4 + 4]
            c = int.from_bytes(chunk, "little")
            m = pow(c, d, n)
            session_aes_key += m.to_bytes(2, "little")

        self.crypto_key = session_aes_key

        self.sendwrapped(Msg(1))
        crypted_hello = self.recvwrapped()
        if crypted_hello.msg_type != 1:
            raise Exception("expected crypted hello")

    def login(self, user: str, passwd: str) -> None:
        # payload = b"delta_star\x00\x00\x00\x00\x00\x00whiskey_demon\x00\x00\x00"
        payload = (
            user.encode()
            + bytes(16 - len(user))
            + passwd.encode()
            + bytes(16 - len(passwd))
        )
        msg = Msg(5, payload=payload)
        self.sendwrapped(msg)
        resp = self.recvwrapped()
        if resp.msg_type != 1:
            raise Exception("login failed")

    def recvmsg(self) -> Msg:
        return Msg.from_socket(self.socket)

    def sendmsg(self, msg: Msg) -> None:
        msg.conn_id = self.conn_id
        msg.to_socket(self.socket)

    def recvwrapped(self) -> Msg:
        msg = self.recvmsg()
        iv = hashlib.md5(self.conn_id.to_bytes(2, "little")).digest()
        return msg.from_wrapped(self.crypto_key, iv)

    def sendwrapped(self, msg: Msg) -> None:
        msg.conn_id = self.conn_id
        iv = hashlib.md5(self.conn_id.to_bytes(2, "little")).digest()
        wrapped = msg.to_wrapped(self.crypto_key, iv)
        self.sendmsg(wrapped)


def flag1(host: str, port: int) -> str:
    x = Conn(host, port)
    x.login("delta_star", "whiskey_demon")

    # construct `x3c/common.Msg{Type: 8}` message and send to get flag
    x.sendwrapped(Msg(8))
    msg = x.recvwrapped()
    flag = msg.payload.decode()

    # clean quit
    x.sendwrapped(Msg(14))
    x.socket.close()

    return flag


def main() -> None:
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
    except Exception:
        print(f"usage: {sys.argv[0]} <host> <port>")
        return

    print(flag1(host, port))


if __name__ == "__main__":
    main()
