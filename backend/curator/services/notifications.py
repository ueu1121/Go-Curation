"""Idempotent notification records. Phase 1 never sends; a retry can never duplicate a send."""
from pymongo.errors import DuplicateKeyError

from ..db import NO_ID, db, iso, new_id
from ..integrations.providers import DisabledNotifier


async def queue_notification(hid: str, kind: str, idempotency_key: str, to: str, subject: str) -> dict:
    existing = await db.notifications.find_one({"idempotency_key": idempotency_key}, NO_ID)
    if existing:
        return {**existing, "replay": True}
    result = DisabledNotifier().send(to, subject, "")
    doc = {"id": new_id(), "household_id": hid, "kind": kind, "idempotency_key": idempotency_key,
           "to": to, "subject": subject, "status": "sent" if result["sent"] else "suppressed",
           "reason": result.get("reason"), "created_at": iso()}
    try:
        await db.notifications.insert_one(dict(doc))
    except DuplicateKeyError:
        return {**(await db.notifications.find_one({"idempotency_key": idempotency_key}, NO_ID)), "replay": True}
    return {**doc, "replay": False}
