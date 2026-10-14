from datetime import timedelta

from ..db import NO_ID, db, iso, new_id, utcnow

RESEARCH_TARGET_H, RESEARCH_DUE_H = 24, 48
OPEN = ("queued", "researching")


async def new_idea(hid, member, description, url, location, preferred_date, kind="idea", input_id=None) -> dict:
    now = utcnow()
    doc = {"id": new_id(), "household_id": hid, "submitted_by": member["id"], "description": description,
           "url": url, "location": location, "preferred_date": preferred_date, "kind": kind, "status": "queued",
           "submitted_at": iso(now), "research_target_at": iso(now + timedelta(hours=RESEARCH_TARGET_H)),
           "research_due_at": iso(now + timedelta(hours=RESEARCH_DUE_H)), "outcome": None,
           "linked_experience_id": None, "source_input_id": input_id, "dataset": "real",
           "url_verified": False, "history": [{"at": iso(now), "status": "queued"}]}
    await db.user_ideas.insert_one(dict(doc))
    return doc


def decorate(idea: dict) -> dict:
    idea["overdue"] = idea["status"] in OPEN and idea["research_due_at"] < iso()
    return idea


async def list_ideas(hid: str) -> list[dict]:
    ideas = await db.user_ideas.find({"household_id": hid}, NO_ID).sort("submitted_at", -1).to_list(500)
    return [decorate(i) for i in ideas]


async def set_outcome(hid: str, idea_id: str, status: str, reason: str | None, linked: str | None, actor: str):
    from fastapi import HTTPException
    if status in ("not_selected", "needs_information", "expired") and not reason:
        raise HTTPException(422, "A reason is required for this status")
    outcome = {"status": status, "reason": reason, "at": iso(), "by": actor}
    res = await db.user_ideas.update_one(
        {"id": idea_id, "household_id": hid},
        {"$set": {"status": status, "outcome": outcome, **({"linked_experience_id": linked} if linked else {})},
         "$push": {"history": {"at": iso(), "status": status, "reason": reason, "by": actor}}})
    if not res.matched_count:
        raise HTTPException(404, "Idea not found")
    return decorate(await db.user_ideas.find_one({"id": idea_id}, NO_ID))
