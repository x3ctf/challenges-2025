from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from secrets import randbits
from typing import Annotated

from Crypto.Util.number import long_to_bytes
from fastapi import Cookie, Depends, HTTPException, Response, status

from mvmcryption.crypto.cipher import XSCBCCipher
from mvmcryption.crypto.ecdsa import ECDSA, private_key
from mvmcryption.crypto.jwt import SJWT
from mvmcryption.crypto.rsa import RSA, PrivKey
from mvmcryption.db.users import User, Users
from mvmcryption.resp import PERMISSION_DENIED

SJWT_TTL = timedelta(minutes=15)


def global_ecdsa(private_key: Annotated[int, Depends(private_key)]) -> ECDSA:
    return ECDSA(private_key)


def global_sjwt(ecdsa: Annotated[ECDSA, Depends(global_ecdsa)]):
    return SJWT(ecdsa)


def create_sjwt(user: User, sjwt: SJWT, expires: datetime | None = None) -> str:
    _expires = expires or (datetime.now(UTC) + SJWT_TTL)
    return sjwt.encode({"sub": user.id, "exp": _expires.isoformat()})


def decode_sjwt(token: str, sjwt: SJWT, users: Users) -> User | None:
    if not token:
        return None
    try:
        decoded = sjwt.decode(token)
    except Exception:
        return None

    if not (
        expiry_str := decoded.get("exp")
    ):  # no expiry -> some token generated by an admin
        return None  # for ~~security~~ budget reasons this is disabled right now # TODO: fix this

    if not isinstance(expiry_str, str):
        return None

    try:
        expiry = datetime.fromisoformat(expiry_str)
    except Exception:
        return None

    if not expiry or expiry <= datetime.now(UTC):
        return None

    user_id = decoded.get("sub")

    if user_id is None:
        return None

    if not isinstance(user_id, int):
        return None

    user = users.find(user_id)

    if user is None:
        return None

    return user


def authorized_user(
    users: Annotated[Users, Depends(Users.dependency)],
    sjwt: Annotated[SJWT, Depends(global_sjwt)],
    response: Response,
    mvmcryptionauthtoken: Annotated[str | None, Cookie()] = None,
):
    user = decode_sjwt(mvmcryptionauthtoken, sjwt, users)
    if not user:
        if mvmcryptionauthtoken:
            response.delete_cookie("mvmcryptionauthtoken")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized.",
        )
    return user


def admin_user(user: Annotated[User, Depends(authorized_user)]):
    if not user.is_admin:
        raise PERMISSION_DENIED
    return user


def _aes_key() -> bytes:
    f = Path("/etc/aes-key")
    if not f.exists():
        f.write_bytes(long_to_bytes(randbits(128)))
    return f.read_bytes()


def global_rsa() -> RSA:
    rsa = RSA(  # hardcoded for speed
        PrivKey(
            43427513068463780395679475519379846953439482983882880632680161345605131667718960623289584552531690451339468396375027415123555230739798154071597331969440327109839308482130942226948288469069504580422637040390736179366054054004136195726195333832861775946760324940445735398700330246847155551414519249931576262451,
            15854537697835921276240629455217071431028016733329619193920226747077103915047288270411347526844176499452476141014594351107801681957161963855318893641419035258597532899645682462209809516728929156279775477900154153329635585057835679897334124129740452933865580783325412346614996486168449797021965646388366333127,
            98011239440242166566698900909182478499579591553994012246543489477537261857225746359620806272924221914643114124037819334121515530197013448069167414820829072829060396211285847063664930352380987263284391101868939020557899449512764006655929361614868808424862362572962982195082292181544684702119281913347793415203,
        )
    )

    assert rsa.verify(b"hello", rsa.sign(b"hello"))
    return rsa


GlobalRSA = Annotated[RSA, Depends(global_rsa)]


def global_aes(
    key: Annotated[bytes, Depends(_aes_key)],
    rsa: GlobalRSA,
):
    return XSCBCCipher(key, rsa)


AuthorizedUser = Annotated[User, Depends(authorized_user)]
AdminUser = Annotated[User, Depends(admin_user)]
GlobalECDSA = Annotated[ECDSA, Depends(global_ecdsa)]
GlobalXSCBCCipher = Annotated[XSCBCCipher, Depends(global_aes)]
