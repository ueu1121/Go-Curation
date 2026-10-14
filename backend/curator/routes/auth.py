from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..config import settings
from ..db import NO_ID, db, local_today, utcnow
from ..integrations.providers import get_interpreter
from ..schemas import DisplayNameIn, LoginIn
from ..security import COOKIE, create_session, current_member, verify_password
from ..services.repo import members_of, public_member

router = APIRouter(prefix="/api", tags=["auth"])


async def _fail(key: str, attempt: dict | None):
    count = (attempt or {}).get("count", 0) + 1
    update = {"count": count, "last_failed_at": utcnow()}
    if count >= settings.login_max_attempts:
        update = {"count": 0, "locked_until": utcnow() + timedelta(minutes=settings.login_lock_minutes)}
    await db.login_attempts.update_one({"key": key}, {"$set": update}, upsert=True)


@router.post("/auth/login")
async def login(body: LoginIn, response: Response):
    email = body.email.strip().lower()
    attempt = await db.login_attempts.find_one({"key": email})
    if attempt and attempt.get("locked_until") and attempt["locked_until"] > utcnow():
        raise HTTPException(429, f"Too many failed attempts. Try again in {settings.login_lock_minutes} minutes.")
    member = await db.members.find_one({"email": email, "active": True})
    if not member or not verify_password(body.password, member["password_hash"]):
        await _fail(email, attempt)
        raise HTTPException(401, "Email or password is incorrect.")
    await db.login_attempts.delete_one({"key": email})
    token, exp = await create_session(member)
    response.set_cookie(COOKIE, token, httponly=True, secure=settings.cookie_secure, samesite="lax",
                        max_age=settings.session_ttl_days * 86400, path="/")
    member["is_admin"] = email in settings.admin_emails
    return {"member": public_member(member), "expires_at": exp.isoformat()}


@router.post("/auth/register")
async def register():
    raise HTTPException(403, "Public sign-up is disabled. Accounts are provisioned by an administrator.")


@router.post("/auth/logout")
async def logout(response: Response, member: dict = Depends(current_member)):
    await db.sessions.delete_one({"id": member["session_id"]})
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/auth/me")
async def me(member: dict = Depends(current_member)):
    hid = member["household_id"]
    hh = await db.households.find_one({"id": hid}, NO_ID)
    interp = get_interpreter()
    return {
        "member": public_member(member),
        "household": {"id": hh["id"], "name": hh["name"]},
        "members": [public_member(m) for m in await members_of(hid)],
        "environment": {"app_env": settings.app_env, "demo_mode": settings.demo_mode,
                        "interpreter": interp.name, "live_ai": interp.live,
                        "timezone": "America/Toronto", "local_date": local_today().isoformat(),
                        "phase": "1 — foundation (no live research, AI, email or scheduling)"},
    }


@router.put("/members/me")
async def rename(body: DisplayNameIn, member: dict = Depends(current_member)):
    await db.members.update_one({"id": member["id"]}, {"$set": {"display_name": body.display_name}})
    return {"ok": True, "display_name": body.display_name}


@router.get("/health")
async def health(request: Request):
    try:
        await db.command("ping")
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "unreachable",
            "app_env": settings.app_env, "demo_mode": settings.demo_mode}
