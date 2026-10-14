import hmac
from datetime import timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request

from .config import settings
from .db import NO_ID, db, new_id, utcnow

COOKIE = "curator_session"
ALG = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


async def create_session(member: dict) -> tuple[str, object]:
    sid = new_id()
    exp = utcnow() + timedelta(days=settings.session_ttl_days)
    await db.sessions.insert_one({"id": sid, "member_id": member["id"], "expires_at": exp, "created_at": utcnow()})
    token = jwt.encode({"sub": member["id"], "sid": sid, "exp": exp, "type": "participant"},
                       settings.jwt_secret, algorithm=ALG)
    return token, exp


def _token(request: Request) -> str | None:
    token = request.cookies.get(COOKIE)
    auth = request.headers.get("Authorization", "")
    if not token and auth.startswith("Bearer "):
        token = auth[7:]
    return token


async def decode_session(request: Request) -> dict | None:
    token = _token(request)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALG])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "participant":
        return None
    session = await db.sessions.find_one({"id": payload.get("sid"), "member_id": payload.get("sub")})
    if not session or session["expires_at"] < utcnow():
        return None
    member = await db.members.find_one({"id": payload["sub"], "active": True}, {**NO_ID, "password_hash": 0})
    if member:
        member["is_admin"] = member["email"] in settings.admin_emails
        member["session_id"] = payload["sid"]
    return member


async def current_member(request: Request) -> dict:
    member = await decode_session(request)
    if not member:
        raise HTTPException(status_code=401, detail="Please sign in again.")
    return member


async def admin_member(member: dict = Depends(current_member)) -> dict:
    if not member["is_admin"]:
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return member


async def automation_household(request: Request) -> str:
    key = request.headers.get("X-Automation-Key", "")
    if not settings.automation_key or not key or not hmac.compare_digest(key, settings.automation_key):
        raise HTTPException(status_code=401, detail="Valid automation key required.")
    hh = await db.households.find_one({"slug": settings.automation_household_slug}, NO_ID)
    if not hh:
        raise HTTPException(status_code=503, detail="Automation household is not configured.")
    return hh["id"]


async def any_household(request: Request) -> str:
    if request.headers.get("X-Automation-Key"):
        return await automation_household(request)
    return (await current_member(request))["household_id"]


async def automation_or_admin(request: Request) -> str:
    if request.headers.get("X-Automation-Key"):
        return await automation_household(request)
    return (await admin_member(await current_member(request)))["household_id"]
