from fastapi import HTTPException

from ..db import NO_ID, db, iso, new_id
from ..domain.scoring import compute_fit_score, evidence_status
from ..domain.validation import normalize_name
from ..schemas import BatchIn, CandidateIn
from ..seed import create_destination
from .repo import check, load_candidate, publication_context, resolve_destination


async def record_run(run_type: str, key: str | None, outcome: str, error: str | None = None, usage=None) -> None:
    await db.automation_runs.insert_one({"id": new_id(), "run_type": run_type, "idempotency_key": key,
                                         "started_at": iso(), "finished_at": iso(), "outcome": outcome,
                                         "error_summary": error, "usage": usage or {}})


async def _destination(hid: str, d) -> tuple[dict, bool]:
    if d.id:
        found = await db.destinations.find_one({"id": d.id, "household_id": hid, "dataset": "real"}, NO_ID)
        if not found:
            raise HTTPException(422, "destination.id does not belong to this household")
        return found, True
    found = await resolve_destination(hid, d.name, d.aliases)
    if found:
        merged = sorted(set(found["aliases"]) | set(d.aliases))
        names = sorted({normalize_name(n) for n in [found["name"], *merged]})
        await db.destinations.update_one({"id": found["id"]}, {"$set": {"aliases": merged, "normalized_names": names}})
        return found, True
    extra = d.model_dump(exclude={"id", "name", "kind"})
    return await create_destination(hid, d.name, d.kind, **extra), False


async def ingest_candidate(hid: str, body: CandidateIn, actor: str) -> dict:
    if body.idempotency_key:
        prior = await db.experiences.find_one({"household_id": hid, "idempotency_key": body.idempotency_key}, NO_ID)
        if prior:
            cand = await load_candidate(hid, prior["id"])
            return {"experience_id": prior["id"], "idempotent_replay": True, "publication_check": await check(hid, cand)}
    fit, score_errors = compute_fit_score(body.score_components)
    if score_errors:
        raise HTTPException(422, {"score_errors": score_errors})
    dest, matched = await _destination(hid, body.destination)
    eid = new_id()
    exp = {"id": eid, "household_id": hid, "dataset": "real", "destination_id": dest["id"],
           **body.experience.model_dump(), "travel": body.travel.model_dump(),
           "score_components": body.score_components, "fit_score": fit, "idempotency_key": body.idempotency_key,
           "research_status": "candidate", "submitted_by": actor, "linked_idea_id": body.linked_idea_id,
           "created_at": iso()}
    await db.experiences.insert_one(dict(exp))
    for o in body.occurrences:
        await db.event_occurrences.insert_one({"id": new_id(), "household_id": hid, "experience_id": eid,
                                               "dataset": "real", **o.model_dump()})
    for e in body.evidence:
        await db.evidence_sources.insert_one({"id": new_id(), "household_id": hid, "experience_id": eid,
                                              **e.model_dump(), "recorded_at": iso(), "recorded_by": actor,
                                              "reviewed_by": None, "reviewed_at": None})
    if body.linked_idea_id:
        await db.user_ideas.update_one({"id": body.linked_idea_id, "household_id": hid},
                                       {"$set": {"linked_experience_id": eid, "status": "researching"}})
    cand = await load_candidate(hid, eid)
    result = await check(hid, cand)
    await record_run("candidate_ingest", body.idempotency_key, "stored")
    return {"experience_id": eid, "destination_id": dest["id"], "destination_matched": matched,
            "fit_score": fit, "evidence_status": evidence_status(cand["evidence"]),
            "publication_check": result, "idempotent_replay": False,
            "note": "Structural validation only. Stored verification states are not independently re-checked."}


async def _batch_response(hid: str, batch: dict, replay: bool, validation=None) -> dict:
    items = await db.batch_items.find({"batch_id": batch["id"]}, NO_ID).sort("rank", 1).to_list(10)
    return {"batch": batch, "items": items, "idempotent_replay": replay, "validation": validation}


async def create_batch(hid: str, body: BatchIn, actor: str) -> dict:
    prior = await db.batches.find_one({"household_id": hid, "idempotency_key": body.idempotency_key}, NO_ID)
    if prior:
        return await _batch_response(hid, prior, True)
    cands = []
    for it in body.items:
        c = await load_candidate(hid, it.experience_id)
        if not c:
            raise HTTPException(422, f"Unknown experience {it.experience_id}")
        c["novelty_explanation"] = it.novelty_explanation or c.get("novelty_explanation")
        c["repeat_exception"] = it.repeat_exception or c.get("repeat_exception")
        cands.append(c)
    if body.status == "insufficient_candidates" and not body.note:
        raise HTTPException(422, "insufficient_candidates requires a note explaining why")
    ctx = await publication_context(hid)
    from ..domain.publication import validate_batch
    validation = validate_batch(cands, ctx, body.status)
    if body.status == "published" and not validation["ok"]:
        await record_run("batch_publish", body.idempotency_key, "rejected", ",".join(validation["batch_errors"]))
        raise HTTPException(422, {"message": "Batch failed publication rules", "validation": validation})
    bid = new_id()
    batch = {"id": bid, "household_id": hid, "dataset": "real", "local_date": body.local_date, "slot": body.slot,
             "status": body.status, "generated_at": iso(),
             "published_at": iso() if body.status in ("published", "insufficient_candidates") else None,
             "idempotency_key": body.idempotency_key, "note": body.note, "created_by": actor}
    await db.batches.insert_one(dict(batch))
    for it, c in zip(body.items, cands):
        snap = {k: v for k, v in c.items() if k != "_id"}
        await db.batch_items.insert_one({"id": new_id(), "batch_id": bid, "household_id": hid, "dataset": "real",
                                         "experience_id": c["id"], "occurrence_id": it.occurrence_id, "rank": it.rank,
                                         "snapshot": snap, "fit_score": c["fit_score"],
                                         "score_components": c["score_components"],
                                         "novelty_explanation": c.get("novelty_explanation"),
                                         "repeat_exception": c.get("repeat_exception")})
        if body.status == "published":
            await db.experiences.update_one({"id": c["id"]}, {"$set": {"research_status": "published"}})
    await record_run("batch_" + body.status, body.idempotency_key, "stored")
    return await _batch_response(hid, batch, False, validation)
