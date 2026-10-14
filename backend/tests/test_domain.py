"""Pure domain-rule tests (no database)."""
from datetime import date, timedelta

import pytest

from curator.domain.geo import haversine_km, policy_distance
from curator.domain.interpreter import interpret
from curator.domain.publication import check_candidate, shared_state, validate_batch
from curator.domain.scoring import WEIGHTS, compute_fit_score
from curator.domain.validation import clean_url, normalize_name

TODAY = date(2026, 10, 14)
POLICY = {"basis": "geographic", "primary_km": 50, "exceptional_km": 90}
GOOD_SOURCE = {"url": "https://example.org/event", "supported_claim": "Event date", "verification_status": "reviewed_supports_claim"}


def cand(**kw):
    base = {"id": "e1", "dataset": "real", "destination_id": "d1", "category": "food", "kind": "evergreen",
            "fit_score": 80, "evidence": [GOOD_SOURCE], "occurrences": [], "travel": {}}
    return {**base, **kw}


def ctx(**kw):
    return {"today": TODAY, "exclusions": [], "recent_proposals": [], "visits": [], "distance_policy": POLICY, **kw}


def test_weights_total_100_and_validation():
    assert sum(WEIGHTS.values()) == 100
    score, errors = compute_fit_score({k: w for k, w in WEIGHTS.items()})
    assert score == 100 and not errors
    _, errors = compute_fit_score({"uniqueness": 30})
    assert "component_out_of_range:uniqueness" in errors and "missing_component:low_crowd" in errors


def test_t09_score_below_70_fails_publication():
    assert "fit_score_below_threshold" in check_candidate(cand(fit_score=69.9), ctx())["errors"]
    assert check_candidate(cand(fit_score=70), ctx())["eligible"]


def test_t08_missing_or_unreviewed_sources_block_publication():
    assert "no_evidence_source" in check_candidate(cand(evidence=[]), ctx())["errors"]
    unreviewed = [{**GOOD_SOURCE, "verification_status": "unverified"}]
    assert "evidence_not_reviewed" in check_candidate(cand(evidence=unreviewed), ctx())["errors"]


def test_t12_demo_records_never_publishable():
    assert "demo_record_not_publishable" in check_candidate(cand(dataset="demo"), ctx())["errors"]


def test_t07_explicit_exclusions_block():
    for ex in ({"scope": "destination", "target_id": "d1"}, {"scope": "experience", "target_id": "e1"},
               {"scope": "category", "category": "food"}):
        assert not check_candidate(cand(), ctx(exclusions=[{**ex, "active": True}]))["eligible"]
    expired = {"scope": "category", "category": "food", "active": True, "expires_on": "2026-10-01"}
    assert check_candidate(cand(), ctx(exclusions=[expired]))["eligible"]


def test_t06_drive_through_does_not_exclude_new_experiences():
    visits = [{"destination_id": "d1", "visit_type": "drive_through"}]
    assert check_candidate(cand(), ctx(visits=visits))["eligible"]
    town = [{"destination_id": "d1", "visit_type": "town_visit"}]
    assert "prior_visit_requires_difference_explanation" in check_candidate(cand(), ctx(visits=town))["errors"]
    assert check_candidate(cand(novelty_explanation="Festival weekend, not a town walk"), ctx(visits=town))["eligible"]


def test_t11_historical_visits_persist_beyond_60_day_window():
    old_proposal = [{"destination_id": "d1", "local_date": (TODAY - timedelta(days=61)).isoformat()}]
    recent = [{"destination_id": "d1", "local_date": (TODAY - timedelta(days=10)).isoformat()}]
    assert check_candidate(cand(), ctx(recent_proposals=old_proposal))["eligible"]
    assert "destination_proposed_within_60_days" in check_candidate(cand(), ctx(recent_proposals=recent))["errors"]
    undated_visit = [{"destination_id": "d1", "visit_type": "experience", "visit_date": None}]
    assert not check_candidate(cand(), ctx(visits=undated_visit))["eligible"]


def test_generic_category_needs_distinct_angle():
    assert "generic_category_requires_distinct_angle" in check_candidate(cand(category="waterfall"), ctx())["errors"]
    assert check_candidate(cand(category="waterfall", distinct_angle="Ice formations only after cold snap"), ctx())["eligible"]


def test_distance_policy_does_not_mix_bases():
    travel = {"geo_distance_km": 40, "driving_distance_km": 70}
    assert policy_distance(travel, POLICY) == 40
    assert policy_distance(travel, {**POLICY, "basis": "driving"}) == 70
    c = cand(travel=travel)
    assert check_candidate(c, ctx())["eligible"]
    assert "beyond_primary_radius_not_labelled_exceptional" in check_candidate(
        c, ctx(distance_policy={**POLICY, "basis": "driving"}))["errors"]
    assert "distance_unknown_on_policy_basis" in check_candidate(cand(), ctx())["warnings"]
    assert 40 < haversine_km(43.33, -79.80, 43.65, -79.38) < 60


def test_expired_events_and_batch_rules():
    past = [{"start_date": "2026-10-01", "end_date": "2026-10-02", "availability_status": "available"}]
    assert "event_expired_or_no_upcoming_occurrence" in check_candidate(cand(kind="dated_event", occurrences=past), ctx())["errors"]
    one = validate_batch([cand()], ctx(), "published")
    assert "published_batch_must_have_2_to_5_items" in one["batch_errors"]
    dup = validate_batch([cand(), cand(id="e2")], ctx(), "published")
    assert "duplicate_destination_in_batch" in dup["batch_errors"]
    ok = validate_batch([cand(), cand(id="e2", destination_id="d2", category="history")], ctx(), "published")
    assert ok["ok"]


def test_shared_state():
    assert shared_state({"a": {"reaction": "interested"}, "b": {"reaction": "interested"}}, ["a", "b"]) == "both_interested"
    assert shared_state({"a": {"reaction": "interested"}, "b": {"reaction": "not_today"}}, ["a", "b"]) == "disagreement"
    assert shared_state({}, ["a", "b"]) == "awaiting"


def test_url_and_name_normalization():
    assert clean_url("HTTPS://Example.ORG/Path#frag") == "https://example.org/Path"
    for bad in ("javascript:alert(1)", "http://user:pw@example.org", "https://localhost/x", "ftp://x.org"):
        with pytest.raises(ValueError):
            clean_url(bad)
    assert normalize_name("Cambridge, Ontario") == normalize_name("cambridge") == "cambridge"


ICTX = {"today": TODAY, "selected_plan": None, "last_visit": {"id": "v1", "title": "Mill tour", "is_demo": False}, "focus_item": None}


def test_interpreter_temporary_defaults_and_clarification():
    r = interpret("Nothing expensive today.", None, ICTX)
    budget = next(c for c in r["proposed_changes"] if c["payload"].get("key") == "budget")
    assert budget["payload"]["scope"] == "today" and "scope" in budget["editable"]
    r = interpret("That was nice, but the walking was too much.", None, ICTX)
    assert r["clarification"] and "less walking for future suggestions" in r["clarification"]["question"]
    r = interpret("We drove through Cambridge, but we did not visit attractions.", None, ICTX)
    assert r["proposed_changes"][0]["payload"]["visit_type"] == "drive_through"
    r = interpret("We went there yesterday", None, ICTX)
    assert r["clarification"] is not None
    r = interpret("I saw this event https://example.org/e would it work for us?", None, ICTX)
    assert r["proposed_changes"][0]["type"] == "create_idea" and r["live_ai"] is False
    r = interpret("purple elephants", None, ICTX)
    assert r["proposed_changes"][0]["type"] == "note"
