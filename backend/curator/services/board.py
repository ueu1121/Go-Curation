from fastapi import HTTPException

from ..db import NO_ID, db, iso, local_today, new_id
from ..domain.publication import shared_state
from .repo import members_of


async def item_views(hid: str, items: list[dict], member_id: str) -> list[dict]:
    member_ids = [m["id"] for m in await members_of(hid)]
    ids = [i["id"] for i in items]
    reacts = await db.reactions.find({"household_id": hid, "batch_item_id": {"$in": ids}}, NO_ID).to_list(500)
    plans = await db.plans.find({"household_id": hid, "batch_item_id": {"$in": ids},
                                 "status": {"$ne": "cancelled"}}, NO_ID).to_list(100)
    exp_ids = [i["experience_id"] for i in items]
    saved = await db.interests.find({"household_id": hid, "experience_id": {"$in": exp_ids}}, NO_ID).to_list(100)
    for it in items:
        r = {x["member_id"]: x for x in reacts if x["batch_item_id"] == it["id"]}
        it["reactions"] = r
        it["shared_state"] = shared_state(r, member_ids)
        it["plan"] = next((p for p in plans if p["batch_item_id"] == it["id"]), None)
        it["saved_by"] = [s["member_id"] for s in saved if s["experience_id"] == it["experience_id"]]
    return items


async def batches_with_items(hid: str, query: dict, member_id: str, limit: int = 2) -> list[dict]:
    batches = await db.batches.find({"household_id": hid, **query}, NO_ID).sort(
        [("local_date", -1), ("generated_at", -1)]).to_list(limit)
    for b in batches:
        items = await db.batch_items.find({"batch_id": b["id"]}, NO_ID).sort("rank", 1).to_list(10)
        b["items"] = await item_views(hid, items, member_id)
    return sorted(batches, key=lambda b: 0 if b["slot"] == "morning" else 1)


async def get_item(hid: str, item_id: str) -> dict:
    item = await db.batch_items.find_one({"id": item_id, "household_id": hid}, NO_ID)
    if not item:
        raise HTTPException(404, "Option not found")
    return item


async def complete_plan(hid: str, member: dict, plan_id: str, visit_date: str | None,
                        precision: str, notes: str | None) -> dict:
    plan = await db.plans.find_one({"id": plan_id, "household_id": hid}, NO_ID)
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan["status"] != "selected":
        raise HTTPException(409, f"Plan is {plan['status']}, not selected")
    visit = {"id": new_id(), "household_id": hid, "destination_id": plan.get("destination_id"),
             "destination_name": plan.get("destination_name"), "experience_id": plan["experience_id"],
             "activity": plan["title"], "category": plan.get("category"), "plan_id": plan_id,
             "visit_type": "experience", "visit_date": visit_date,
             "date_precision": precision if visit_date else "unknown", "user_reported": True,
             "historical": False, "needs_confirmation": False, "notes": notes, "dataset": plan["dataset"],
             "recorded_by": member["id"], "created_at": iso()}
    await db.visits.insert_one(dict(visit))
    await db.plans.update_one({"id": plan_id}, {"$set": {"status": "completed", "completed_at": iso(),
                                                         "visit_id": visit["id"]}})
    return visit


def today_iso() -> str:
    return local_today().isoformat()
