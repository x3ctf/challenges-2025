import asyncio
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_hex

import httpx
from Crypto.Util.number import long_to_bytes
from cryptoattacks.attacks.cbc.padding_oracle import attack
from cryptoattacks.attacks.hnp.lattice_attack import dsa_known_msb
from cryptoattacks.shared.partial_integer import PartialInteger
from fastecdsa.curve import P256
from mvmcryption.crypto.ecdsa import ECDSA, decode_signature
from mvmcryption.crypto.jwt import SJWT
from mvmcryption.utils import decode, encode
from randcrack import RandCrack
from sage.all import *

username = token_hex(16)
password = token_hex(16)

API_URL = "http://localhost:8000/api"


def submit_randbits128(cracker: RandCrack, value: int) -> RandCrack:
    for i in range(4):
        randbits32 = (value >> (i * 32)) & 0xFFFFFFFF
        cracker.submit(randbits32)
    return cracker


async def register(
    c: httpx.AsyncClient, username: str, password: str
) -> httpx.Response:
    return await c.post(
        f"{API_URL}/auth/register",
        json={
            "username": username,
            "password": password,
            "email": token_hex(10) + "@" + "example.com",
        },
    )


async def login(c: httpx.AsyncClient, username: str, password: str) -> httpx.Response:
    return await c.post(
        f"{API_URL}/auth/login", json={"username": username, "password": password}
    )


async def jwt_to_h_r_s(c: httpx.AsyncClient):
    jwt = c.cookies.get("mvmcryptionauthtoken")
    assert jwt
    parts = jwt.split(".")
    body = parts[0]
    r, s = parts[1:]
    return int(sha256(decode(body)).hexdigest(), 16), decode_signature((r, s))


def sync_jwt_to_h_r_s(c: httpx.Client):
    jwt = c.cookies.get("mvmcryptionauthtoken")
    assert jwt
    parts = jwt.split(".")
    body = parts[0]
    r, s = parts[1:]
    return int(sha256(decode(body)).hexdigest(), 16), decode_signature((r, s))


async def get_public_key(c: httpx.AsyncClient) -> dict:
    resp = await c.get(f"{API_URL}/crypto/public-key", timeout=20000)
    return resp.json()


def get_next_nonce(secret_key: int):
    c = httpx.Client()
    c.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
    h, (r, s) = sync_jwt_to_h_r_s(c)
    s_inv = pow(s, -1, P256.q)
    k = ((h + r * secret_key) * s_inv) % P256.q
    assert k

    return k


def decrypt(c: httpx.Client, ct: bytes, sig: int, iv: bytes) -> dict:
    resp = c.post(
        f"{API_URL}/crypto/decrypt",
        json={
            "ciphertext": encode(ct),
            "iv": encode(iv),
            "signature": hex(sig),
            "debug": True,
        },
    )

    return resp.json()


async def main():
    collection = []
    async with httpx.AsyncClient() as c:
        public_key = await get_public_key(c)
        await register(c, username, password)
        for _ in range(5):
            await login(c, username, password)
            collection.append(await jwt_to_h_r_s(c))

    pint = PartialInteger()
    pint.add_known(0, 128)
    pint.add_unknown(128)

    # even tho it would be fun doing this manually, there really is no need for this large of a bias
    hs, rs, ss = [], [], []
    for h, (r, s) in collection:
        hs.append(h)
        rs.append(r)
        ss.append(s)

    private_key, _ = list(dsa_known_msb(P256.q, hs, rs, ss, [pint] * len(hs)))[0]

    ecdsa = ECDSA(private_key)
    assert ecdsa.pretty_public_key == public_key

    sjwt = SJWT(ecdsa)

    admin_token = sjwt.encode(
        {"sub": 1, "exp": (datetime.now(UTC) + timedelta(days=600)).isoformat()}
    )

    c = httpx.Client(cookies={"mvmcryptionauthtoken": admin_token})

    cracker = RandCrack()
    for _ in range((624 // (128 // 32))):
        cracker = submit_randbits128(cracker, get_next_nonce(private_key))

    assert get_next_nonce(private_key) == cracker.predict_getrandbits(128)
    assert cracker.predict_getrandbits(128) == get_next_nonce(private_key)
    assert cracker.predict_getrandbits(128) == get_next_nonce(private_key)

    enc_flag = c.get(f"{API_URL}/crypto/flag").json()
    flag_ct, flag_sig = decode(enc_flag["ciphertext"]), int(enc_flag["signature"], 16)
    flag_iv = long_to_bytes(cracker.predict_getrandbits(128), 16)

    def do_oracle(iv, ct):
        resp = decrypt(c, ct, flag_sig, iv)
        return resp == {}

    assert do_oracle(flag_iv, flag_ct)

    print(attack(do_oracle, flag_iv, flag_ct))


if __name__ == "__main__":
    asyncio.run(main())
