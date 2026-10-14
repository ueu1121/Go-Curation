from fastapi import APIRouter, Depends, HTTPException

from ..config import OPTIONAL_ENV, REQUIRED_ENV, settings
from ..db import NO_ID, clean, db, iso
from ..integrations.providers import provider_status
from ..migrations import LATEST
from ..schemas import BatchIn, CandidateIn, EvidenceReviewIn, IdeaOutcomeIn
from ..security import admin_member
from ..seed import seed_demo
from ..services.ideas import list_ideas, set_outcome
from ..services.ingest import create_batch, ingest_candidate
from ..services.repo import check, load_candidate, publication_context

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def setup_report() -> dict:
    import os
    try:
        await db.command("ping")
        db_ok = True
    except Exception:
        db_ok = False
    applied = [m["name"] for m in await db.schema_migrations.find({}, NO_ID).to_list(100)] if db_ok else []
    accounts = await db.members.count_documents({"active": True}) if db_ok else 0
    placeholder = await db.members.count_documents({"active": True, "email": {"$regex": r"\.invalid$"}}) if db_ok else 0
    checks = [
        {"check": "required_env", "ok": all(os.environ.get(n) for n in REQUIRED_ENV),
         "detail": {n: bool(os.environ.get(n)) for n in REQUIRED_ENV}},
        {"check": "optional_env", "ok": True, "detail": {n: bool(os.environ.get(n)) for n in OPTIONAL_ENV}},
        {"check": "database", "ok": db_ok, "detail": "reachable" if db_ok else "unreachable"},
        {"check": "migrations", "ok": LATEST in applied, "detail": {"latest": LATEST, "applied": applied}},
        {"check": "jwt_secret_strength", "ok": len(settings.jwt_secret) >= 32, "detail": "length >= 32"},
        {"check": "participant_accounts", "ok": 1 <= accounts <= 2, "detail": f"{accounts} active account(s)"},
        {"check": "admin_configured", "ok": bool(settings.admin_emails), "detail": "ADMIN_EMAILS set"},
        {"check": "automation_key", "ok": len(settings.automation_key) >= 24, "detail": "AUTOMATION_API_KEY >= 24 chars"},
        {"check": "production_safety", "ok": not (settings.app_env == "production" and (settings.dev_accounts() or placeholder)),
         "detail": "no dev/placeholder accounts or demo mode in production"},
    ]
    return {"ok": all(c["ok"] for c in checks), "checks": checks, "providers": provider_status(),
            "app_env": settings.app_env, "demo_mode": settings.demo_mode}


@router.get("/setup-check")
async def setup_check(_: dict = Depends(admin_member)):
    return await setup_report()


@router.get("/status")
async def status(member: dict = Depends(admin_member)):
    hid = member["household_id"]
    ideas = await list_ideas(hid)
    return {
        "last_successful_run": await db.automation_runs.find_one({"outcome": "stored"}, NO_ID, sort=[("finished_at", -1)]),
        "failed_runs": await db.automation_runs.find({"outcome": {"$in": ["rejected", "failed"]}}, NO_ID)
        .sort("finished_at", -1).to_list(20),
        "last_published_batch": await db.batches.find_one({"household_id": hid, "dataset": "real", "status": "published"},
                                                          NO_ID, sort=[("published_at", -1)]),
        "overdue_ideas": [i for i in ideas if i["overdue"]],
        "open_ideas": [i for i in ideas if i["status"] in ("queued", "researching")],
        "providers": provider_status(),
        "notifications": await db.notifications.find({"household_id": hid}, NO_ID).sort("created_at", -1).to_list(20),
        "checked_at": iso(),
    }


@router.get("/candidates")
async def list_candidates(member: dict = Depends(admin_member)):
    hid = member["household_id"]
    ctx = await publication_context(hid)
    out = []
    for e in await db.experiences.find({"household_id": hid, "dataset": "real"}, NO_ID).sort("created_at", -1).to_list(200):
        cand = await load_candidate(hid, e["id"])
        out.append({**cand, "publication_check": await check(hid, cand, ctx)})
    return {"items": out}


@router.post("/candidates")
async def add_candidate(body: CandidateIn, member: dict = Depends(admin_member)):
    return await ingest_candidate(member["household_id"], body, f"admin:{member['id']}")


@router.patch("/evidence/{evidence_id}")
async def review_evidence(evidence_id: str, body: EvidenceReviewIn, member: dict = Depends(admin_member)):
    res = await db.evidence_sources.update_one(
        {"id": evidence_id, "household_id": member["household_id"]},
        {"$set": {"verification_status": body.verification_status, "review_note": body.note,
                  "reviewed_by": member["id"], "reviewed_at": iso()}})
    if not res.matched_count:
        raise HTTPException(404, "Evidence not found")
    updated = await db.evidence_sources.find_one({"id": evidence_id}, NO_ID)
    return clean(updated)


@router.post("/batches")
async def admin_batch(body: BatchIn, member: dict = Depends(admin_member)):
    return await create_batch(member["household_id"], body, f"admin:{member['id']}")


@router.patch("/ideas/{idea_id}")
async def idea_status(idea_id: str, body: IdeaOutcomeIn, member: dict = Depends(admin_member)):
    return await set_outcome(member["household_id"], idea_id, body.status, body.reason,
                             body.linked_experience_id, f"admin:{member['id']}")


@router.post("/demo/reset")
async def reset_demo(member: dict = Depends(admin_member)):
    if not settings.demo_mode:
        raise HTTPException(409, "Demo mode is off")
    await seed_demo(member["household_id"], force=True)
    return {"ok": True}
