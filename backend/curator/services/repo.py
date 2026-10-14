"""Repository-style helpers shared by routes and services."""
from datetime import date, timedelta

from ..db import NO_ID, db, local_today
from ..domain.publication import DEDUP_DAYS, check_candidate
from ..domain.scoring import evidence_status
from ..domain.validation import normalize_name


async def members_of(hid: str) -> list[dict]:
    return await db.members.find({"household_id": hid, "active": True},
                                 {**NO_ID, "password_hash": 0}).to_list(10)


def public_member(m: dict) -> dict:
    return {"id": m["id"], "display_name": m["display_name"], "email": m["email"],
            "is_admin": m.get("is_admin", False), "personal_preferences": m.get("personal_preferences", {})}


async def load_candidate(hid: str, exp_id: str) -> dict | None:
    exp = await db.experiences.find_one({"id": exp_id, "household_id": hid}, NO_ID)
    if not exp:
        return None
    exp["evidence"] = await db.evidence_sources.find({"experience_id": exp_id}, NO_ID).to_list(50)
    exp["occurrences"] = await db.event_occurrences.find({"experience_id": exp_id}, NO_ID).to_list(50)
    exp["destination"] = await db.destinations.find_one({"id": exp["destination_id"]}, NO_ID)
    exp["evidence_status"] = evidence_status(exp["evidence"])
    return exp


async def publication_context(hid: str, today: date | None = None) -> dict:
    today = today or local_today()
    prefs = await db.preferences.find_one({"household_id": hid}, NO_ID)
    cutoff = (today - timedelta(days=DEDUP_DAYS)).isoformat()
    recent = await db.batch_items.aggregate([
        {"$match": {"household_id": hid, "dataset": "real"}},
        {"$lookup": {"from": "batches", "localField": "batch_id", "foreignField": "id", "as": "b"}},
        {"$unwind": "$b"},
        {"$match": {"b.status": "published", "b.local_date": {"$gte": cutoff}}},
        {"$project": {"_id": 0, "destination_id": "$snapshot.destination_id", "local_date": "$b.local_date"}},
    ]).to_list(500)
    return {
        "today": today,
        "exclusions": await db.exclusions.find({"household_id": hid, "active": True}, NO_ID).to_list(500),
        "recent_proposals": recent,
        "visits": await db.visits.find({"household_id": hid, "dataset": "real"}, NO_ID).to_list(2000),
        "distance_policy": prefs["distance_policy"],
    }


async def check(hid: str, cand: dict, ctx: dict | None = None) -> dict:
    return check_candidate(cand, ctx or await publication_context(hid))


async def resolve_destination(hid: str, name: str, aliases: list[str] | None = None) -> dict | None:
    names = [normalize_name(n) for n in [name, *(aliases or [])] if n]
    return await db.destinations.find_one(
        {"household_id": hid, "dataset": "real", "normalized_names": {"$in": names}}, NO_ID)
