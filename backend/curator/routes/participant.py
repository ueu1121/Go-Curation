from fastapi import APIRouter, Body, Depends, HTTPException

from ..db import NO_ID, clean, db, iso, local_today, new_id
from ..schemas import ClarifyIn, ExclusionIn, IdeaIn, InputConfirm, InputIn, InsightPatch
from ..security import current_member
from ..services import inputs as inbox
from ..services.ideas import list_ideas, new_idea

router = APIRouter(prefix="/api", tags=["participant"])

PREF_FIELDS = {"origin", "distance_policy", "availability", "interests", "avoidances", "effort_tolerance",
               "budget", "walking_tolerance", "accessibility_needs", "dietary", "tie_break_rule",
               "crowd_preference", "outing_shape"}


@router.get("/ideas")
async def ideas(member: dict = Depends(current_member)):
    return {"items": await list_ideas(member["household_id"])}


@router.post("/ideas")
async def submit_idea(body: IdeaIn, member: dict = Depends(current_member)):
    return await new_idea(member["household_id"], member, body.description, body.url, body.location,
                          body.preferred_date)


@router.get("/preferences")
async def get_prefs(member: dict = Depends(current_member)):
    prefs = await db.preferences.find_one({"household_id": member["household_id"]}, NO_ID)
    return clean(prefs)


@router.put("/preferences")
async def put_prefs(body: dict = Body(...), member: dict = Depends(current_member)):
    unknown = set(body) - PREF_FIELDS
    if unknown:
        raise HTTPException(422, f"Unknown preference fields: {sorted(unknown)}")
    policy = body.get("distance_policy")
    if policy and (policy.get("basis") not in ("geographic", "driving")
                   or not 0 < policy.get("primary_km", 0) <= policy.get("exceptional_km", 0) <= 300):
        raise HTTPException(422, "distance_policy needs basis geographic|driving and 0 < primary <= exceptional <= 300")
    log = {"at": iso(), "member_id": member["id"], "fields": sorted(body)}
    await db.preferences.update_one({"household_id": member["household_id"]},
                                    {"$set": {**body, "updated_at": iso(), "updated_by": member["id"]},
                                     "$push": {"change_log": log}})
    return await get_prefs(member)


@router.put("/preferences/personal")
async def put_personal(body: dict = Body(...), member: dict = Depends(current_member)):
    allowed = {"walking_tolerance", "notes", "effort_tolerance"}
    if set(body) - allowed:
        raise HTTPException(422, f"Allowed personal fields: {sorted(allowed)}")
    clean = {f"personal_preferences.{k}": str(v)[:300] for k, v in body.items()}
    await db.members.update_one({"id": member["id"]}, {"$set": clean})
    return {"ok": True}


@router.get("/exclusions")
async def exclusions(member: dict = Depends(current_member)):
    return {"items": await db.exclusions.find({"household_id": member["household_id"]}, NO_ID).to_list(500)}


@router.post("/exclusions")
async def add_exclusion(body: ExclusionIn, member: dict = Depends(current_member)):
    if body.scope == "category" and not body.category:
        raise HTTPException(422, "category is required for a category exclusion")
    if body.scope != "category" and not body.target_id:
        raise HTTPException(422, "target_id is required")
    if body.temporary and not body.expires_on:
        raise HTTPException(422, "A temporary exclusion needs expires_on")
    doc = {"id": new_id(), "household_id": member["household_id"], **body.model_dump(), "active": True,
           "created_by": member["id"], "created_at": iso()}
    await db.exclusions.insert_one(dict(doc))
    return doc


@router.delete("/exclusions/{ex_id}")
async def remove_exclusion(ex_id: str, member: dict = Depends(current_member)):
    await db.exclusions.update_one({"id": ex_id, "household_id": member["household_id"]},
                                   {"$set": {"active": False, "removed_by": member["id"], "removed_at": iso()}})
    return {"ok": True}


@router.get("/insights")
async def insights(member: dict = Depends(current_member)):
    hid = member["household_id"]
    items = await db.insights.find({"household_id": hid, "status": {"$ne": "dismissed"}}, NO_ID).to_list(500)
    now = iso()
    for i in items:
        i["expired"] = bool(i.get("expires_at") and i["expires_at"] < now)
    return clean({"items": items, "local_date": local_today().isoformat()})


@router.patch("/insights/{insight_id}")
async def patch_insight(insight_id: str, body: InsightPatch, member: dict = Depends(current_member)):
    hid = member["household_id"]
    ins = await db.insights.find_one({"id": insight_id, "household_id": hid}, NO_ID)
    if not ins:
        raise HTTPException(404, "Not found")
    if ins["audience"] == "personal" and ins["member_id"] != member["id"]:
        raise HTTPException(403, "Only the owner can change a personal preference")
    update: dict = {}
    if body.action == "dismiss":
        update = {"status": "dismissed"}
    elif body.action == "accept":
        if ins["status"] == "awaiting_partner" and ins["member_id"] == member["id"]:
            raise HTTPException(409, "The other participant needs to accept a shared preference you proposed")
        update = {"status": "active", "kind": "confirmed" if ins["kind"] == "tentative" else ins["kind"]}
    elif body.text:
        update = {"text": body.text}
    await db.insights.update_one({"id": insight_id}, {"$set": update, "$push": {
        "history": {"at": iso(), "member_id": member["id"], "action": body.action, "before": ins.get("text")}}})
    updated = await db.insights.find_one({"id": insight_id}, NO_ID)
    return clean(updated)


@router.get("/inputs")
async def list_inputs(member: dict = Depends(current_member)):
    return {"items": await db.curator_inputs.find({"household_id": member["household_id"]}, NO_ID)
            .sort("created_at", -1).to_list(50)}


@router.post("/inputs")
async def create_input(body: InputIn, member: dict = Depends(current_member)):
    return await inbox.create_input(member["household_id"], member, body.text, body.url, body.context_ref)


@router.post("/inputs/{input_id}/clarify")
async def clarify(input_id: str, body: ClarifyIn, member: dict = Depends(current_member)):
    return await inbox.clarify(member["household_id"], member, input_id, body.choice_id)


@router.post("/inputs/{input_id}/confirm")
async def confirm(input_id: str, body: InputConfirm, member: dict = Depends(current_member)):
    return await inbox.confirm(member["household_id"], member, input_id, body.changes)


@router.post("/inputs/{input_id}/cancel")
async def cancel(input_id: str, member: dict = Depends(current_member)):
    return await inbox.cancel(member["household_id"], member, input_id)
