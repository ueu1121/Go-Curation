"""Versioned, append-only MongoDB migrations. Never edit an applied migration; add a new one."""
from pymongo import ASCENDING

from .db import utcnow


async def m0001_indexes(db):
    await db.households.create_index("id", unique=True)
    await db.households.create_index("slug", unique=True)
    await db.members.create_index("id", unique=True)
    await db.members.create_index("email", unique=True)
    await db.sessions.create_index("id", unique=True)
    await db.sessions.create_index("expires_at", expireAfterSeconds=0)
    await db.login_attempts.create_index("key", unique=True)
    await db.preferences.create_index("household_id", unique=True)
    for coll in ("destinations", "experiences", "event_occurrences", "evidence_sources", "batches",
                 "batch_items", "plans", "visits", "user_ideas", "exclusions", "insights",
                 "curator_inputs", "notes", "source_registry"):
        await db[coll].create_index("id", unique=True)
        await db[coll].create_index("household_id")
    await db.destinations.create_index([("household_id", ASCENDING), ("normalized_names", ASCENDING)])
    partial = {"idempotency_key": {"$type": "string"}}
    await db.batches.create_index([("household_id", ASCENDING), ("idempotency_key", ASCENDING)],
                                  unique=True, partialFilterExpression=partial)
    await db.experiences.create_index([("household_id", ASCENDING), ("idempotency_key", ASCENDING)],
                                      unique=True, partialFilterExpression=partial)
    await db.batch_items.create_index("batch_id")
    await db.reactions.create_index([("member_id", ASCENDING), ("batch_item_id", ASCENDING)], unique=True)
    await db.visit_feedback.create_index([("member_id", ASCENDING), ("visit_id", ASCENDING)], unique=True)
    await db.interests.create_index([("member_id", ASCENDING), ("experience_id", ASCENDING)], unique=True)
    await db.notifications.create_index("idempotency_key", unique=True)
    await db.automation_runs.create_index([("run_type", ASCENDING), ("idempotency_key", ASCENDING)])
    await db.seed_markers.create_index("key", unique=True)


MIGRATIONS = [("0001_indexes", m0001_indexes)]
LATEST = MIGRATIONS[-1][0]


async def run_migrations(db) -> list[str]:
    applied = []
    for name, fn in MIGRATIONS:
        if await db.schema_migrations.find_one({"name": name}):
            continue
        await fn(db)
        await db.schema_migrations.insert_one({"name": name, "applied_at": utcnow()})
        applied.append(name)
    return applied
