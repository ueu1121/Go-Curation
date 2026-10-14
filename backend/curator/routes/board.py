from fastapi import APIRouter, Depends, HTTPException

from ..config import settings
from ..db import NO_ID, clean, db, iso, local_today, new_id
from ..schemas import FeedbackIn, InterestIn, PlanIn, ReactionIn, VisitIn
from ..security import any_household, current_member
from ..services.board import batches_with_items, complete_plan, get_item

router = APIRouter(prefix="/api", tags=["board"])
PHASE_NOTICE = ("Phase 1 foundation: options are demo examples or manually entered records. "
                "No live discovery is running.")


@router.get("/board/today")
async def today(member: dict = Depends(current_member)):
    hid = member["household_id"]
    local = local_today().isoformat()
    real = await batches_with_items(hid, {"dataset": "real", "local_date": local,
                                          "status": {"$in": ["published", "insufficient_candidates"]}}, member["id"])
    mode, batches = ("live", real) if real else ("empty", [])
    if not real and settings.demo_mode:
        batches = await batches_with_items(hid, {"dataset": "demo"}, member["id"])
        mode = "demo" if batches else "empty"
    return {"local_date": local, "timezone": "America/Toronto", "mode": mode, "batches": batches,
            "phase_notice": PHASE_NOTICE}


@router.get("/batches/latest")
async def latest(hid: str = Depends(any_household)):
    batch = await db.batches.find_one({"household_id": hid, "dataset": "real", "status": "published"}, NO_ID,
                                      sort=[("published_at", -1)])
    if not batch:
        return {"batch": None, "items": []}
    items = await db.batch_items.find({"batch_id": batch["id"]}, NO_ID).sort("rank", 1).to_list(10)
    return clean({"batch": batch, "items": items})


@router.post("/reactions")
async def react(body: ReactionIn, member: dict = Depends(current_member)):
    hid = member["household_id"]
    await get_item(hid, body.batch_item_id)
    await db.reactions.update_one(
        {"member_id": member["id"], "batch_item_id": body.batch_item_id},
        {"$set": {"household_id": hid, "reaction": body.reaction, "reason": body.reason, "at": iso()},
         "$push": {"history": {"reaction": body.reaction, "reason": body.reason, "at": iso()}}},
        upsert=True)
    saved = await db.reactions.find_one({"member_id": member["id"], "batch_item_id": body.batch_item_id},
                                        {**NO_ID, "history": 0})
    return clean(saved)


@router.post("/plans")
async def select_plan(body: PlanIn, member: dict = Depends(current_member)):
    hid = member["household_id"]
    item = await get_item(hid, body.batch_item_id)
    if await db.plans.find_one({"batch_item_id": item["id"], "status": "selected"}):
        raise HTTPException(409, "This option is already our plan")
    snap = item["snapshot"]
    plan = {"id": new_id(), "household_id": hid, "batch_item_id": item["id"], "experience_id": item["experience_id"],
            "destination_id": snap.get("destination_id"),
            "destination_name": (snap.get("destination") or {}).get("name"), "title": snap["title"],
            "category": snap.get("category"), "planned_date": body.planned_date or local_today().isoformat(),
            "status": "selected", "selected_by": member["id"], "selected_at": iso(), "dataset": item["dataset"]}
    await db.plans.insert_one(dict(plan))
    return plan


@router.post("/plans/{plan_id}/cancel")
async def cancel_plan(plan_id: str, member: dict = Depends(current_member)):
    res = await db.plans.update_one({"id": plan_id, "household_id": member["household_id"], "status": "selected"},
                                    {"$set": {"status": "cancelled", "cancelled_by": member["id"], "cancelled_at": iso()}})
    if not res.matched_count:
        raise HTTPException(404, "No selected plan with that id")
    return {"ok": True}


@router.post("/visits")
async def record_visit(body: VisitIn, member: dict = Depends(current_member)):
    precision = "day" if body.visit_date else "unknown"
    return await complete_plan(member["household_id"], member, body.plan_id, body.visit_date, precision, body.notes)


@router.post("/visits/{visit_id}/feedback")
async def feedback(visit_id: str, body: FeedbackIn, member: dict = Depends(current_member)):
    hid = member["household_id"]
    if not await db.visits.find_one({"id": visit_id, "household_id": hid}):
        raise HTTPException(404, "Visit not found")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    await db.visit_feedback.update_one({"visit_id": visit_id, "member_id": member["id"]},
                                       {"$set": {"household_id": hid, **fields, "updated_at": iso()}}, upsert=True)
    saved = await db.visit_feedback.find_one({"visit_id": visit_id, "member_id": member["id"]}, NO_ID)
    return clean(saved)


@router.post("/interests")
async def toggle_interest(body: InterestIn, member: dict = Depends(current_member)):
    hid = member["household_id"]
    if not await db.experiences.find_one({"id": body.experience_id, "household_id": hid}):
        raise HTTPException(404, "Experience not found")
    key = {"member_id": member["id"], "experience_id": body.experience_id}
    if await db.interests.find_one(key):
        await db.interests.delete_one(key)
        return {"saved": False}
    await db.interests.insert_one({**key, "household_id": hid, "note": body.note, "at": iso()})
    return {"saved": True}


@router.get("/upcoming")
async def upcoming(member: dict = Depends(current_member)):
    hid = member["household_id"]
    datasets = ["real", "demo"] if settings.demo_mode else ["real"]
    occs = await db.event_occurrences.find({"household_id": hid, "dataset": {"$in": datasets},
                                            "start_date": {"$gte": local_today().isoformat()}},
                                           NO_ID).sort("start_date", 1).to_list(200)
    exp_ids = list({o["experience_id"] for o in occs})
    exps = {e["id"]: e for e in await db.experiences.find(
        {"id": {"$in": exp_ids}, "research_status": {"$in": ["demo", "candidate", "eligible", "published"]}},
        NO_ID).to_list(200)}
    saved = await db.interests.find({"household_id": hid, "experience_id": {"$in": exp_ids}}, NO_ID).to_list(200)
    out = []
    for o in occs:
        e = exps.get(o["experience_id"])
        if e:
            out.append({"occurrence": o, "experience": e,
                        "saved_by": [s["member_id"] for s in saved if s["experience_id"] == e["id"]]})
    return {"items": out, "local_date": local_today().isoformat()}


@router.get("/history")
async def history(member: dict = Depends(current_member)):
    hid = member["household_id"]
    offered = await db.batch_items.aggregate([
        {"$match": {"household_id": hid}},
        {"$lookup": {"from": "batches", "localField": "batch_id", "foreignField": "id", "as": "b"}},
        {"$unwind": "$b"},
        {"$project": {"_id": 0, "id": 1, "dataset": 1, "title": "$snapshot.title", "category": "$snapshot.category",
                      "local_date": "$b.local_date", "slot": "$b.slot", "batch_status": "$b.status"}},
        {"$sort": {"local_date": -1}}]).to_list(500)
    visits = await db.visits.find({"household_id": hid}, NO_ID).sort("created_at", -1).to_list(1000)
    fb = await db.visit_feedback.find({"household_id": hid}, NO_ID).to_list(2000)
    for v in visits:
        v["feedback"] = [f for f in fb if f["visit_id"] == v["id"]]
    reactions = await db.reactions.find({"household_id": hid, "reaction": {"$in": ["not_today", "not_for_us"]}},
                                        {**NO_ID, "history": 0}).to_list(1000)
    titles = {o["id"]: o["title"] for o in offered}
    for r in reactions:
        r["title"] = titles.get(r["batch_item_id"])
    return clean({
        "offered": offered,
        "plans": await db.plans.find({"household_id": hid}, NO_ID).sort("selected_at", -1).to_list(500),
        "visits": visits,
        "rejections": reactions,
        "exclusions": await db.exclusions.find({"household_id": hid}, NO_ID).to_list(500),
    })
