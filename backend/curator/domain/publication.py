from datetime import date, timedelta

from .geo import policy_distance
from .scoring import PUBLISH_THRESHOLD, VERIFIED_STATES

DEDUP_DAYS = 60
GENERIC_CATEGORIES = {"park", "waterfall", "conservation_area", "trail"}
BATCH_MIN, BATCH_MAX = 2, 5


def _active(ex: dict, today: date) -> bool:
    exp = ex.get("expires_on")
    return ex.get("active", True) and (not exp or date.fromisoformat(exp) >= today)


def _excluded(c: dict, exclusions: list[dict], today: date) -> list[str]:
    hits = []
    for ex in exclusions:
        if not _active(ex, today):
            continue
        scope = ex.get("scope")
        if scope == "destination" and ex.get("target_id") == c.get("destination_id"):
            hits.append("excluded:destination")
        elif scope == "experience" and ex.get("target_id") == c.get("id"):
            hits.append("excluded:experience")
        elif scope == "category" and ex.get("category") == c.get("category"):
            hits.append("excluded:category")
    return hits


def _evidence_errors(c: dict) -> list[str]:
    sources = c.get("evidence") or []
    if not sources:
        return ["no_evidence_source"]
    with_url = [s for s in sources if s.get("url")]
    if not with_url:
        return ["no_source_url"]
    if not any(s.get("verification_status") in VERIFIED_STATES for s in with_url):
        return ["evidence_not_reviewed"]
    return []


def _history_errors(c: dict, ctx: dict, today: date) -> list[str]:
    errors = []
    dest = c.get("destination_id")
    explained = bool(c.get("repeat_exception") or c.get("novelty_explanation"))
    cutoff = today - timedelta(days=DEDUP_DAYS)
    for p in ctx.get("recent_proposals", []):
        if p.get("destination_id") == dest and date.fromisoformat(p["local_date"]) >= cutoff:
            if not c.get("repeat_exception"):
                errors.append("destination_proposed_within_60_days")
            break
    for v in ctx.get("visits", []):
        if v.get("destination_id") != dest or v.get("visit_type") == "drive_through":
            continue
        if not explained:
            errors.append("prior_visit_requires_difference_explanation")
        break
    return errors


def _occurrence_errors(c: dict, today: date) -> list[str]:
    if c.get("kind") != "dated_event":
        return []
    live = [
        o for o in c.get("occurrences") or []
        if o.get("availability_status") != "cancelled"
        and date.fromisoformat(o.get("end_date") or o["start_date"]) >= today
    ]
    return [] if live else ["event_expired_or_no_upcoming_occurrence"]


def _distance_checks(c: dict, policy: dict) -> tuple[list[str], list[str]]:
    dist = policy_distance(c.get("travel") or {}, policy)
    if dist is None:
        return [], ["distance_unknown_on_policy_basis"]
    if dist > policy.get("exceptional_km", 90):
        return ["beyond_exceptional_radius"], []
    if dist > policy.get("primary_km", 50) and not c.get("exceptional_distance"):
        return ["beyond_primary_radius_not_labelled_exceptional"], []
    return [], []


def check_candidate(c: dict, ctx: dict) -> dict:
    today = ctx["today"]
    errors: list[str] = []
    warnings: list[str] = []
    if c.get("dataset") != "real":
        errors.append("demo_record_not_publishable")
    if (c.get("fit_score") or 0) < PUBLISH_THRESHOLD:
        errors.append("fit_score_below_threshold")
    errors += _evidence_errors(c)
    errors += _excluded(c, ctx.get("exclusions", []), today)
    errors += _history_errors(c, ctx, today)
    errors += _occurrence_errors(c, today)
    if c.get("category") in GENERIC_CATEGORIES and not c.get("distinct_angle"):
        errors.append("generic_category_requires_distinct_angle")
    d_err, d_warn = _distance_checks(c, ctx.get("distance_policy", {}))
    errors += d_err
    warnings += d_warn
    return {"eligible": not errors, "errors": errors, "warnings": warnings}


def validate_batch(candidates: list[dict], ctx: dict, status: str) -> dict:
    results = [{"experience_id": c.get("id"), **check_candidate(c, ctx)} for c in candidates]
    batch_errors, warnings = [], []
    if status == "published":
        if not BATCH_MIN <= len(candidates) <= BATCH_MAX:
            batch_errors.append("published_batch_must_have_2_to_5_items")
        dests = [c.get("destination_id") for c in candidates]
        if len(dests) != len(set(dests)):
            batch_errors.append("duplicate_destination_in_batch")
        if len({c.get("category") for c in candidates}) < 2:
            warnings.append("fewer_than_two_categories")
        if any(not r["eligible"] for r in results):
            batch_errors.append("one_or_more_items_not_eligible")
    ok = not batch_errors if status == "published" else True
    return {"ok": ok, "items": results, "batch_errors": batch_errors, "warnings": warnings}


def shared_state(reactions: dict, member_ids: list[str]) -> str:
    values = [reactions.get(m, {}).get("reaction") for m in member_ids]
    if values and all(v == "interested" for v in values):
        return "both_interested"
    if "interested" in values and any(v in ("not_today", "not_for_us") for v in values):
        return "disagreement"
    if any(values):
        return "partial"
    return "awaiting"
