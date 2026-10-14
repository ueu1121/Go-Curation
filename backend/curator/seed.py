"""Idempotent seeding: household, shared preferences, user-reported history, dev accounts, demo data."""
import logging

from .config import settings
from .db import db, iso, local_date_offset, local_today, new_id, NO_ID
from .domain.scoring import compute_fit_score
from .domain.validation import normalize_name
from .security import hash_password

log = logging.getLogger("curator.seed")

DEFAULT_PREFERENCES = {
    "origin": {"label": "Burlington, ON — city centre (provisional)", "precision": "city",
               "lat": None, "lng": None, "status": "provisional",
               "note": "Exact origin not provided. Coordinates unset until confirmed."},
    "distance_policy": {"basis": "geographic", "primary_km": 50, "exceptional_km": 90,
                        "exceptional_requires_label": True},
    "availability": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                     "depart_after": "13:00", "return_by": "21:00",
                     "note": "Availability window, not a target to fill."},
    "timezone": "America/Toronto",
    "interests": ["nature", "wildlife", "history", "culture", "scenic drives", "food",
                  "seasonal activities", "lightly adventurous"],
    "avoidances": ["generic shopping malls", "bars/clubs as the main outing", "crowded theme parks",
                   "loud family entertainment centres", "over-touristed spots without a distinct angle",
                   "elaborate multi-stop itineraries", "repeated generic parks/waterfalls/conservation areas"],
    "crowd_preference": "calm, lower-crowd",
    "outing_shape": "One main stop; backups and food stops optional",
    "effort_tolerance": "unspecified",
    "budget": {"status": "unspecified", "max_for_two": None},
    "walking_tolerance": "unspecified",
    "accessibility_needs": "unspecified",
    "dietary": "unspecified",
    "tie_break_rule": "none — decide together",
}

HISTORY = [
    ("Lowville Park", "park", "experience", "Fish migration viewing", "nature",
     "Location interpreted as Lowville Park; original wording unclear. Needs confirmation.", True),
    ("Hidden Valley", "park", "experience", "Fish migration viewing", "nature",
     "Exact park/location needs confirmation.", True),
    ("Little Canada", "attraction", "experience", None, None, "Activities not specified.", False),
    ("Paris, Ontario", "town", "town_visit", None, None, "Town visit; specific activities unknown.", False),
    ("Elora, Ontario", "town", "town_visit", None, None, "Town visit; specific activities unknown.", False),
    ("Niagara Falls, Ontario", "town", "town_visit", None, None, "Visit; specific activities unknown.", False),
    ("Milton, Ontario", "town", "drive_through", None, None, "Drive through only.", False),
    ("Cambridge, Ontario", "town", "drive_through", None, None, "Drive through only.", False),
    ("Caledonia, Ontario", "town", "drive_through", None, None, "Drive through only.", False),
]
BROAD_NOTES = [
    ("waterfall", "Many/all waterfalls visited; individual names not yet provided."),
    ("park", "Many parks visited; individual names not yet provided."),
    ("conservation_area", "Three conservation areas visited; names not yet provided."),
]


async def _once(key: str) -> bool:
    if await db.seed_markers.find_one({"key": key}):
        return False
    await db.seed_markers.insert_one({"key": key, "at": iso()})
    return True


async def ensure_household(slug: str = "primary", name: str = "Our household") -> str:
    hh = await db.households.find_one({"slug": slug}, NO_ID)
    if hh:
        return hh["id"]
    hid = new_id()
    await db.households.insert_one({"id": hid, "slug": slug, "name": name, "created_at": iso()})
    await db.preferences.insert_one({"household_id": hid, **DEFAULT_PREFERENCES, "updated_at": iso(),
                                     "updated_by": None, "change_log": []})
    return hid


async def create_destination(hid: str, name: str, kind: str, dataset: str = "real", **extra) -> dict:
    doc = {"id": new_id(), "household_id": hid, "name": name, "aliases": extra.pop("aliases", []),
           "kind": kind, "locality": extra.pop("locality", None), "lat": None, "lng": None,
           "coordinates_verified": False, "external_ids": {}, "dataset": dataset,
           "needs_confirmation": extra.pop("needs_confirmation", False), "created_at": iso(), **extra}
    doc["normalized_names"] = sorted({normalize_name(n) for n in [name, *doc["aliases"]]})
    await db.destinations.insert_one(dict(doc))
    return doc


async def seed_history(hid: str):
    if not await _once(f"history:{hid}"):
        return
    for name, kind, vtype, activity, category, note, confirm in HISTORY:
        dest = await create_destination(hid, name, kind, needs_confirmation=confirm)
        await db.visits.insert_one({
            "id": new_id(), "household_id": hid, "destination_id": dest["id"], "destination_name": name,
            "experience_id": None, "activity": activity, "category": category, "plan_id": None,
            "visit_type": vtype, "visit_date": None, "date_precision": "unknown", "user_reported": True,
            "historical": True, "needs_confirmation": confirm, "notes": note, "dataset": "real",
            "created_at": iso()})
    for category, note in BROAD_NOTES:
        await db.visits.insert_one({
            "id": new_id(), "household_id": hid, "destination_id": None, "destination_name": None,
            "experience_id": None, "activity": None, "category": category, "plan_id": None,
            "visit_type": "broad_note", "visit_date": None, "date_precision": "unknown",
            "user_reported": True, "historical": True, "needs_confirmation": False, "notes": note,
            "dataset": "real", "created_at": iso()})


async def provision_member(hid: str, email: str, password: str, display_name: str, reset: bool = False) -> str:
    email = email.strip().lower()
    existing = await db.members.find_one({"email": email})
    if existing and not reset:
        return "exists"
    if existing:
        await db.members.update_one({"email": email}, {"$set": {"password_hash": hash_password(password)}})
        await db.sessions.delete_many({"member_id": existing["id"]})
        return "reset"
    count = await db.members.count_documents({"household_id": hid, "active": True})
    if count >= 2:
        raise ValueError("Household already has two participants")
    await db.members.insert_one({"id": new_id(), "household_id": hid, "email": email,
                                 "display_name": display_name, "password_hash": hash_password(password),
                                 "active": True, "personal_preferences": {"walking_tolerance": "unspecified"},
                                 "created_at": iso()})
    return "created"


def _demo_experience(hid: str, dest_id: str, title: str, category: str, effort: str, **kw) -> dict:
    comps = kw.pop("components")
    fit, _ = compute_fit_score(comps)
    return {
        "id": new_id(), "household_id": hid, "dataset": "demo", "destination_id": dest_id,
        "title": title, "category": category, "kind": kw.pop("kind", "evergreen"), "effort": effort,
        "indoor": kw.pop("indoor", None), "description": kw.pop("description"),
        "why_now": kw.pop("why_now"), "why_unique": kw.pop("why_unique", None),
        "fit_explanation": kw.pop("fit", None), "hidden_perk": kw.pop("perk", None),
        "best_timing": kw.pop("timing", None), "duration_estimate": kw.pop("duration", None),
        "suggested_window": kw.pop("window", None),
        "cost_for_two": kw.pop("cost", {"min": None, "max": None, "currency": "CAD", "status": "unknown"}),
        "crowd_guidance": kw.pop("crowd", None), "crowd_level": kw.pop("crowd_level", None),
        "booking": kw.pop("booking", {"required": None, "deadline": None, "notes": None}),
        "accessibility_notes": kw.pop("access", None), "weather_notes": kw.pop("weather", None),
        "nearby_backup": kw.pop("backup", None), "distinct_angle": kw.pop("angle", None),
        "novelty_explanation": None, "repeat_exception": None,
        "travel": {"origin_label": "Burlington, ON — city centre (provisional)", "geo_distance_km": None,
                   "geo_method": None, "driving_distance_km": None, "driving_duration_min": None,
                   "measurement_source": None, "status": "unknown"},
        "unknowns": kw.pop("unknowns", []), "verification_notes": "Synthetic demo record. Not researched.",
        "score_components": comps, "fit_score": fit, "evidence": [], "occurrences": kw.pop("occurrences", []),
        "research_status": "demo", "exceptional_distance": False, "created_at": iso(),
    }


DEMO_ITEMS = [
    dict(title="Demo · Small-batch smokehouse tasting", category="food", effort="easy", indoor=False,
         description="Synthetic example of a food event card.", why_now="Example: a limited weekend tasting.",
         why_unique="Example text showing where the unique angle would appear.",
         fit="Example: food interest, one main stop.", perk="Example perk text.", duration="About 2 hours (example)",
         window="2 PM – 5 PM (example)", crowd="Unknown — no evidence", unknowns=["Price", "Exact hours", "Travel time"],
         components={"uniqueness": 18, "low_crowd": 10, "preference_fit": 12, "timing": 12, "evidence": 0, "practicality": 7}),
    dict(title="Demo · Heritage mill open day", category="history", effort="moderate", indoor=True,
         description="Synthetic example of a rare-opening card.", why_now="Example: opens to the public twice a year.",
         why_unique="Example: a working mechanism rarely shown.", fit="Example: history interest, calm pace.",
         duration="1–1.5 hours (example)", crowd="Expected quieter on weekdays (example wording only)", crowd_level="low",
         cost={"min": 0, "max": 20, "currency": "CAD", "status": "estimate"}, access="Example: stairs to the upper floor.",
         unknowns=["Booking requirement", "Travel time"],
         components={"uniqueness": 22, "low_crowd": 15, "preference_fit": 12, "timing": 13, "evidence": 0, "practicality": 6}),
    dict(title="Demo · Dusk heron-rookery viewing", category="wildlife", effort="easy", indoor=False,
         description="Synthetic example of a quiet-nature card with a distinct reason to go.",
         why_now="Example: nesting season window.", angle="Example: a time-limited wildlife behaviour, not a generic park.",
         fit="Example: wildlife interest, low effort.", weather="Example: check wind and rain.",
         duration="About 1 hour (example)", crowd="Unknown — no evidence", unknowns=["Exact location", "Access rules"],
         components={"uniqueness": 20, "low_crowd": 16, "preference_fit": 13, "timing": 14, "evidence": 0, "practicality": 5}),
    dict(title="Demo · Letterpress studio demonstration", category="maker", effort="easy", indoor=True,
         description="Synthetic example of a maker experience.", why_now="Example: monthly public demonstration.",
         fit="Example: culture and maker interest.", duration="About 90 minutes (example)",
         cost={"min": 30, "max": 50, "currency": "CAD", "status": "estimate"}, crowd_level="low",
         crowd="Expected small group based on example capacity (illustrative)", unknowns=["Travel time"],
         components={"uniqueness": 19, "low_crowd": 15, "preference_fit": 11, "timing": 9, "evidence": 0, "practicality": 7}),
    dict(title="Demo · Orchard cider-pressing afternoon", category="seasonal", effort="moderate", indoor=False,
         description="Synthetic example of a seasonal card.", why_now="Example: short pressing season.",
         fit="Example: seasonal and food interests.", duration="2 hours (example)", crowd="Unknown — no evidence",
         unknowns=["Price", "Hours", "Travel time"],
         components={"uniqueness": 15, "low_crowd": 9, "preference_fit": 12, "timing": 15, "evidence": 0, "practicality": 6}),
]

DEMO_UPCOMING = [
    dict(title="Demo · Regional BBQ festival (example)", category="food", effort="moderate", kind="dated_event",
         description="Synthetic example of an upcoming dated event.", why_now="Example: one weekend only.",
         booking={"required": True, "deadline": local_date_offset(9), "notes": "Example: timed tickets."},
         unknowns=["Ticket price", "Parking", "Travel time"], days=(12, 13),
         components={"uniqueness": 16, "low_crowd": 6, "preference_fit": 13, "timing": 14, "evidence": 0, "practicality": 6}),
    dict(title="Demo · Observatory public night (example)", category="science", effort="easy", kind="dated_event",
         description="Synthetic example of an infrequent opening.", why_now="Example: monthly, weather permitting.",
         booking={"required": None, "deadline": None, "notes": None}, unknowns=["Booking", "Travel time"], days=(20, 20),
         components={"uniqueness": 20, "low_crowd": 14, "preference_fit": 12, "timing": 12, "evidence": 0, "practicality": 5}),
]


async def _demo_batch(hid: str, slot: str, exps: list[dict]):
    bid = new_id()
    await db.batches.insert_one({"id": bid, "household_id": hid, "dataset": "demo", "local_date": local_today().isoformat(),
                                 "slot": slot, "status": "demo_preview", "generated_at": iso(), "published_at": None,
                                 "idempotency_key": None, "note": "Synthetic demo batch for layout testing."})
    for rank, exp in enumerate(exps, start=1):
        await db.batch_items.insert_one({"id": new_id(), "batch_id": bid, "household_id": hid, "dataset": "demo",
                                         "experience_id": exp["id"], "occurrence_id": None, "rank": rank,
                                         "snapshot": {k: v for k, v in exp.items() if k != "_id"},
                                         "fit_score": exp["fit_score"], "score_components": exp["score_components"],
                                         "novelty_explanation": None, "repeat_exception": None})


async def seed_demo(hid: str, force: bool = False):
    if force:
        for coll in ("experiences", "destinations", "event_occurrences", "batches", "batch_items"):
            await db[coll].delete_many({"household_id": hid, "dataset": "demo"})
        await db.seed_markers.delete_one({"key": f"demo:{hid}"})
    if not await _once(f"demo:{hid}"):
        return
    exps = []
    for spec in DEMO_ITEMS + DEMO_UPCOMING:
        spec = dict(spec)
        days = spec.pop("days", None)
        dest = await create_destination(hid, f"Demo location for {spec['title']}", "demo", dataset="demo")
        exp = _demo_experience(hid, dest["id"], **spec)
        if days:
            occ = {"id": new_id(), "household_id": hid, "experience_id": exp["id"], "dataset": "demo",
                   "start_date": local_date_offset(days[0]), "end_date": local_date_offset(days[1]),
                   "start_time": None, "end_time": None, "timezone": "America/Toronto",
                   "availability_status": "unknown", "booking_deadline": exp["booking"].get("deadline")}
            await db.event_occurrences.insert_one(dict(occ))
            exp["occurrences"] = [occ]
        await db.experiences.insert_one(dict(exp))
        exps.append(exp)
    await _demo_batch(hid, "morning", exps[:3])
    await _demo_batch(hid, "midday", exps[3:5])


async def run_seed():
    hid = await ensure_household()
    await seed_history(hid)
    for acct in settings.dev_accounts():
        result = await provision_member(hid, acct["email"], acct["password"], acct["display_name"])
        log.info("dev account %s: %s", acct["display_name"], result)
    if settings.demo_mode:
        await seed_demo(hid)
    return hid
