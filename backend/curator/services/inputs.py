from fastapi import HTTPException

from ..db import NO_ID, db, end_of_local_day, iso, local_today, new_id
from ..integrations.providers import ProviderUnavailable, get_interpreter
from ..domain.validation import clean_text
from ..seed import create_destination
from .board import complete_plan
from .ideas import new_idea
from .repo import resolve_destination


async def interpreter_context(hid: str, context_ref: dict | None) -> dict:
    plan = await db.plans.find_one({"household_id": hid, "status": "selected"}, NO_ID, sort=[("selected_at", -1)])
    recent = await db.visits.find({"household_id": hid, "historical": False}, NO_ID).sort("created_at", -1).to_list(3)
    visit = recent[0] if recent else None
    focus = None
    if context_ref and context_ref.get("batch_item_id"):
        item = await db.batch_items.find_one({"id": context_ref["batch_item_id"], "household_id": hid}, NO_ID)
        if item:
            focus = {"experience_id": item["experience_id"], "title": item["snapshot"]["title"]}
    return {
        "today": local_today(),
        "selected_plan": {"id": plan["id"], "title": plan["title"]} if plan else None,
        "last_visit": {"id": visit["id"], "title": visit.get("activity") or visit.get("destination_name") or "last outing",
                       "is_demo": visit["dataset"] == "demo"} if visit else None,
        "recent_visits": [{"id": v["id"], "title": v.get("activity") or v.get("destination_name") or "outing",
                           "is_demo": v["dataset"] == "demo"} for v in recent],
        "focus_item": focus,
    }


def _number(changes: list[dict]) -> list[dict]:
    return [{"selected": True, "editable": [], **c, "id": f"c{i + 1}"} for i, c in enumerate(changes)]


async def _answer(hid: str, query: str) -> list[dict]:
    words = [w for w in query.replace("?", " ").split() if len(w) > 3 and w not in
             ("there", "coming", "anything", "event", "events", "something", "would", "could")]
    if not words:
        return []
    rx = "|".join(words)
    found = await db.experiences.find({"household_id": hid, "$or": [
        {"title": {"$regex": rx, "$options": "i"}}, {"category": {"$regex": rx, "$options": "i"}},
        {"description": {"$regex": rx, "$options": "i"}}]}, NO_ID).to_list(10)
    return [{"experience_id": f["id"], "title": f["title"], "dataset": f["dataset"],
             "research_status": f["research_status"]} for f in found]


async def create_input(hid: str, member: dict, text: str, url: str | None, context_ref: dict | None) -> dict:
    ctx = await interpreter_context(hid, context_ref)
    degraded = None
    try:
        result = get_interpreter().interpret(text, url, ctx)
    except ProviderUnavailable as exc:
        degraded = str(exc)
        result = {"provider": "unavailable", "live_ai": False, "intents": ["general_note"],
                  "interpretation": "Interpreter unavailable; saved as a note for later.",
                  "proposed_changes": _number([{"type": "note", "summary": "Save as a note", "payload": {"text": text}}]),
                  "clarification": None}
    for ch in result["proposed_changes"]:
        if ch["type"] == "answer_question":
            ch["payload"]["answer"] = await _answer(hid, ch["payload"]["query"])
    doc = {"id": new_id(), "household_id": hid, "member_id": member["id"], "original_text": text,
           "url": url, "modality": "text", "context_refs": context_ref or {}, **result,
           "status": "needs_clarification" if result["clarification"] else "awaiting_confirmation",
           "applied_changes": [], "degraded": degraded, "created_at": iso(), "audit": [{"at": iso(), "event": "received"}]}
    await db.curator_inputs.insert_one(dict(doc))
    return doc


async def clarify(hid: str, member: dict, input_id: str, choice_id: str) -> dict:
    doc = await _get(hid, input_id)
    choice = next((c for c in (doc.get("clarification") or {}).get("choices", []) if c["id"] == choice_id), None)
    if not choice:
        raise HTTPException(422, "Unknown clarification choice")
    changes = _number([c for c in doc["proposed_changes"] if c["type"] != "note"] + choice["changes"])
    await db.curator_inputs.update_one({"id": input_id}, {
        "$set": {"proposed_changes": changes, "status": "awaiting_confirmation",
                 "clarification.resolved_choice": choice_id},
        "$push": {"audit": {"at": iso(), "event": f"clarified:{choice_id}", "member_id": member["id"]}}})
    return await _get(hid, input_id)


async def _get(hid: str, input_id: str) -> dict:
    doc = await db.curator_inputs.find_one({"id": input_id, "household_id": hid}, NO_ID)
    if not doc:
        raise HTTPException(404, "Input not found")
    return doc


async def _insight(hid, member, p, kind, input_id) -> dict:
    audience = p.get("audience", "shared")
    temporary = p.get("scope") == "today"
    status = "active"
    if not temporary and audience == "shared" and kind == "confirmed":
        status = "awaiting_partner"
    doc = {"id": new_id(), "household_id": hid, "kind": "temporary" if temporary else kind,
           "key": p.get("key"), "value": p.get("value"), "text": p.get("text") or f"{p.get('key')}: {p.get('value')}",
           "audience": audience, "member_id": member["id"], "status": status, "reason": p.get("reason"),
           "source_input_id": input_id, "expires_at": end_of_local_day(local_today()) if temporary else None,
           "created_at": iso(), "history": []}
    await db.insights.insert_one(dict(doc))
    return {"insight_id": doc["id"], "status": status}


async def _visit_from_place(hid, member, p, input_id) -> dict:
    dest = await resolve_destination(hid, p["place"])
    if not dest:
        kind = "town" if p["visit_type"] == "drive_through" else "unknown"
        dest = await create_destination(hid, p["place"], kind, needs_confirmation=True)
    vid = new_id()
    await db.visits.insert_one({"id": vid, "household_id": hid, "destination_id": dest["id"],
                                "destination_name": dest["name"], "experience_id": None, "activity": None,
                                "category": None, "plan_id": None, "visit_type": p["visit_type"],
                                "visit_date": p.get("visit_date"), "date_precision": p.get("date_precision", "unknown"),
                                "user_reported": True, "historical": True, "needs_confirmation": True,
                                "notes": None, "dataset": "real", "recorded_by": member["id"],
                                "source_input_id": input_id, "created_at": iso()})
    return {"visit_id": vid, "destination_id": dest["id"]}


async def _feedback(hid, member, p) -> dict:
    visit = await db.visits.find_one({"id": p["visit_id"], "household_id": hid}, NO_ID)
    if not visit:
        raise HTTPException(404, "Visit not found")
    update = {"$set": {"household_id": hid, "updated_at": iso()}}
    if "rating" in p:
        update["$set"]["rating"] = p["rating"]
    else:
        update["$push"] = {"aspects": {"aspect": p["aspect"], "sentiment": p["sentiment"],
                                       "liked_overall": p.get("liked_overall")}}
    await db.visit_feedback.update_one({"visit_id": p["visit_id"], "member_id": member["id"]}, update, upsert=True)
    return {"visit_id": p["visit_id"]}


async def _apply(hid, member, ch, input_id) -> dict:
    t, p = ch["type"], ch["payload"]
    if t == "create_idea":
        idea = await new_idea(hid, member, p.get("description") or "", p.get("url"), None, None,
                              p.get("kind", "idea"), input_id)
        return {"idea_id": idea["id"]}
    if t == "historical_visit":
        return await _visit_from_place(hid, member, p, input_id)
    if t == "complete_plan":
        v = await complete_plan(hid, member, p["plan_id"], p.get("visit_date"), p.get("date_precision", "unknown"), None)
        return {"visit_id": v["id"]}
    if t in ("visit_feedback", "visit_rating"):
        return await _feedback(hid, member, p)
    if t == "set_constraint":
        return await _insight(hid, member, p, "confirmed", input_id)
    if t == "set_preference":
        return await _insight(hid, member, p, "confirmed", input_id)
    if t == "tentative_observation":
        return await _insight(hid, member, {**p, "audience": "shared", "scope": "permanent"}, "tentative", input_id)
    if t == "save_interest":
        await db.interests.update_one({"member_id": member["id"], "experience_id": p["experience_id"]},
                                      {"$set": {"household_id": hid, "note": p.get("note"), "at": iso()}}, upsert=True)
        return {"saved": p["experience_id"]}
    if t == "note":
        nid = new_id()
        await db.notes.insert_one({"id": nid, "household_id": hid, "member_id": member["id"],
                                   "text": p["text"], "kind": p.get("kind", "general"),
                                   "source_input_id": input_id, "created_at": iso()})
        return {"note_id": nid}
    return {"noop": True}


EDITABLE = {"scope": ("today", "permanent"), "audience": ("shared", "personal")}


async def confirm(hid: str, member: dict, input_id: str, edits: list) -> dict:
    doc = await _get(hid, input_id)
    if doc["status"] != "awaiting_confirmation":
        raise HTTPException(409, f"Input is {doc['status']}")
    by_id = {e.id: e for e in edits}
    applied = []
    for ch in doc["proposed_changes"]:
        e = by_id.get(ch["id"])
        if not e or not e.selected:
            continue
        for k, v in (e.payload or {}).items():
            if k not in ch.get("editable", []):
                continue
            if k == "text" and isinstance(v, str) and v.strip():
                ch["payload"]["text"] = clean_text(v, 300)
            elif v in EDITABLE.get(k, ()):
                ch["payload"][k] = v
        applied.append({"change_id": ch["id"], "type": ch["type"], "payload": ch["payload"],
                        "result": await _apply(hid, member, ch, input_id)})
    status = "applied" if applied else "saved_unapplied"
    await db.curator_inputs.update_one({"id": input_id}, {
        "$set": {"status": status, "applied_changes": applied, "confirmed_by": member["id"], "confirmed_at": iso()},
        "$push": {"audit": {"at": iso(), "event": "confirmed", "member_id": member["id"], "count": len(applied)}}})
    return await _get(hid, input_id)


async def cancel(hid: str, member: dict, input_id: str) -> dict:
    await _get(hid, input_id)
    await db.curator_inputs.update_one({"id": input_id}, {
        "$set": {"status": "cancelled"},
        "$push": {"audit": {"at": iso(), "event": "cancelled", "member_id": member["id"]}}})
    return await _get(hid, input_id)
