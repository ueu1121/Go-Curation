"""API tests against an isolated test database (curator_pytest)."""
from zoneinfo import ZoneInfo
from datetime import datetime

from curator.seed import ensure_household, provision_member
from tests.conftest import login

REVIEWED = {"url": "https://example.org/official", "supported_claim": "Dates and hours", "source_type": "official",
            "verification_status": "reviewed_supports_claim"}
SCORES = {"uniqueness": 22, "low_crowd": 15, "preference_fit": 12, "timing": 12, "evidence": 12, "practicality": 7}


def candidate(name, category, **over):
    body = {"destination": {"name": name}, "experience": {"title": f"Test {name}", "category": category, "kind": "evergreen",
            "description": "Test record"}, "evidence": [REVIEWED], "score_components": SCORES}
    body.update(over)
    return body


def demo_items(client, h):
    return [i for b in client.get("/api/board/today", headers=h).json()["batches"] for i in b["items"]]


def test_auth_no_public_signup_and_unauthenticated_writes_rejected(client):
    assert client.post("/api/auth/register", json={}).status_code == 403
    for path in ("/api/reactions", "/api/plans", "/api/visits", "/api/ideas", "/api/inputs", "/api/exclusions"):
        assert client.post(path, json={}).status_code == 401, path
    for path in ("/api/candidates", "/api/batches"):
        assert client.post(path, json={}).status_code == 401, path
    assert client.get("/api/curation-context").status_code == 401


def test_participant_session_cannot_use_automation_endpoints(client, a):
    assert client.get("/api/curation-context", headers=a).status_code == 401
    assert client.post("/api/candidates", headers=a, json=candidate("X", "food")).status_code == 401


def test_t13_toronto_local_date(client, a):
    me = client.get("/api/auth/me", headers=a).json()
    assert me["environment"]["timezone"] == "America/Toronto"
    assert me["environment"]["local_date"] == datetime.now(ZoneInfo("America/Toronto")).date().isoformat()


def test_t10_unknown_travel_and_dates_stay_unknown(client, a):
    items = demo_items(client, a)
    assert items and all(i["dataset"] == "demo" for i in items)
    for i in items:
        t = i["snapshot"]["travel"]
        assert t["geo_distance_km"] is None and t["driving_duration_min"] is None and t["status"] == "unknown"
    low = next(i for i in items if i["fit_score"] < 70)
    assert low["fit_score"] == 59
    visits = client.get("/api/history", headers=a).json()["visits"]
    assert visits and all(v["visit_date"] is None and v["date_precision"] == "unknown" for v in visits if v["historical"])


def test_t02_t03_independent_reactions_and_not_today_is_not_a_block(client, a, b):
    item = demo_items(client, a)[0]["id"]
    client.post("/api/reactions", headers=a, json={"batch_item_id": item, "reaction": "interested"})
    client.post("/api/reactions", headers=b, json={"batch_item_id": item, "reaction": "not_today"})
    found = next(i for i in demo_items(client, a) if i["id"] == item)
    assert {r["reaction"] for r in found["reactions"].values()} == {"interested", "not_today"}
    assert found["shared_state"] == "disagreement"
    assert client.get("/api/exclusions", headers=a).json()["items"] == []
    client.post("/api/reactions", headers=b, json={"batch_item_id": item, "reaction": "interested"})
    found = next(i for i in demo_items(client, a) if i["id"] == item)
    assert found["shared_state"] == "both_interested" and found["plan"] is None


def test_t04_select_does_not_complete_and_feedback_is_per_participant(client, a, b):
    item = demo_items(client, a)[1]["id"]
    plan = client.post("/api/plans", headers=a, json={"batch_item_id": item}).json()
    assert plan["status"] == "selected"
    assert not any(v.get("plan_id") == plan["id"] for v in client.get("/api/history", headers=a).json()["visits"])
    visit = client.post("/api/visits", headers=b, json={"plan_id": plan["id"], "visit_date": None}).json()
    assert visit["date_precision"] == "unknown" and visit["dataset"] == "demo"
    client.post(f"/api/visits/{visit['id']}/feedback", headers=a, json={"rating": 5})
    client.post(f"/api/visits/{visit['id']}/feedback", headers=b, json={"rating": 3, "notes": "crowded"})
    v = next(x for x in client.get("/api/history", headers=a).json()["visits"] if x["id"] == visit["id"])
    assert sorted(f["rating"] for f in v["feedback"]) == [3, 5]
    plans = client.get("/api/history", headers=a).json()["plans"]
    assert next(p for p in plans if p["id"] == plan["id"])["status"] == "completed"


def test_t01_household_isolation(client, a):
    hid = client.portal.call(ensure_household, "other-household", "Other")
    client.portal.call(provision_member, hid, "other@example.invalid", "other-pass", "Other person")
    other = login(client, "other@example.invalid", "other-pass")
    a_item = demo_items(client, a)[0]["id"]
    assert client.post("/api/reactions", headers=other, json={"batch_item_id": a_item, "reaction": "interested"}).status_code == 404
    assert client.post("/api/plans", headers=other, json={"batch_item_id": a_item}).status_code == 404
    assert client.get("/api/board/today", headers=other).json()["mode"] == "empty"
    assert client.get("/api/history", headers=other).json()["visits"] == []
    idea = client.post("/api/ideas", headers=a, json={"description": "A-only idea"}).json()
    assert all(i["id"] != idea["id"] for i in client.get("/api/ideas", headers=other).json()["items"])


def test_t14_ideas_keep_deadlines_and_outcomes(client, a, auto):
    idea = client.post("/api/ideas", headers=a, json={"description": "Maple demo", "url": "https://example.org/maple"}).json()
    assert idea["status"] == "queued" and idea["research_due_at"] > idea["research_target_at"] > idea["submitted_at"]
    assert client.post(f"/api/automation/ideas/{idea['id']}/outcome", headers=auto,
                       json={"status": "not_selected"}).status_code == 422
    r = client.post(f"/api/automation/ideas/{idea['id']}/outcome", headers=auto,
                    json={"status": "not_selected", "reason": "Ends before your window"}).json()
    assert r["outcome"]["reason"] == "Ends before your window" and r["research_due_at"] == idea["research_due_at"]
    assert client.post("/api/ideas", headers=a, json={"description": "bad", "url": "javascript:alert(1)"}).status_code == 422


def test_inputs_preserve_wording_and_temporary_stays_temporary(client, a):
    text = "Something easy this afternoon, not another waterfall."
    inp = client.post("/api/inputs", headers=a, json={"text": text}).json()
    assert inp["original_text"] == text and inp["live_ai"] is False
    edits = [{"id": c["id"], "selected": True} for c in inp["proposed_changes"]]
    done = client.post(f"/api/inputs/{inp['id']}/confirm", headers=a, json={"changes": edits}).json()
    assert done["status"] == "applied"
    insights = client.get("/api/insights", headers=a).json()["items"]
    assert insights and all(i["kind"] == "temporary" and i["expires_at"] for i in insights)


def test_ambiguous_completion_requires_clarification(client, a):
    inp = client.post("/api/inputs", headers=a, json={"text": "We went there yesterday."}).json()
    assert inp["status"] == "needs_clarification"
    assert client.post(f"/api/inputs/{inp['id']}/confirm", headers=a, json={"changes": []}).status_code == 409
    clarified = client.post(f"/api/inputs/{inp['id']}/clarify", headers=a, json={"choice_id": "note_only"}).json()
    assert clarified["status"] == "awaiting_confirmation" and clarified["original_text"] == "We went there yesterday."


def test_personal_vs_shared_attribution_and_learning_corrections(client, a, b):
    inp = client.post("/api/inputs", headers=a, json={"text": "We want one main stop and maybe food nearby."}).json()
    cid = inp["proposed_changes"][0]["id"]
    client.post(f"/api/inputs/{inp['id']}/confirm", headers=a,
                json={"changes": [{"id": cid, "selected": True, "payload": {"scope": "permanent", "audience": "shared"}}]})
    ins = next(i for i in client.get("/api/insights", headers=a).json()["items"] if i["key"] == "outing_shape")
    assert ins["status"] == "awaiting_partner"
    assert client.patch(f"/api/insights/{ins['id']}", headers=a, json={"action": "accept"}).status_code == 409
    assert client.patch(f"/api/insights/{ins['id']}", headers=b, json={"action": "accept"}).json()["status"] == "active"
    inp = client.post("/api/inputs", headers=b, json={"text": "I prefer quiet museums"}).json()
    client.post(f"/api/inputs/{inp['id']}/confirm", headers=b, json={"changes": [{"id": "c1", "selected": True}]})
    mine = next(i for i in client.get("/api/insights", headers=b).json()["items"] if i["audience"] == "personal")
    assert client.patch(f"/api/insights/{mine['id']}", headers=a, json={"action": "dismiss"}).status_code == 403
    edited = client.patch(f"/api/insights/{mine['id']}", headers=b, json={"action": "edit", "text": "Quiet small museums"}).json()
    assert edited["text"] == "Quiet small museums"
    client.patch(f"/api/insights/{mine['id']}", headers=b, json={"action": "dismiss"})
    assert all(i["id"] != mine["id"] for i in client.get("/api/insights", headers=b).json()["items"])


def test_walking_feedback_flow(client, a, b):
    text = "That was nice, but the walking was too much."
    inp = client.post("/api/inputs", headers=b, json={"text": text}).json()
    ids = [c["id"] for c in inp["clarification"]["choices"]]
    assert any(i.startswith("about_visit_") for i in ids) and "future_limit" in ids and "note_only" in ids
    fut = client.post(f"/api/inputs/{inp['id']}/clarify", headers=b, json={"choice_id": "future_limit"}).json()
    ch = fut["proposed_changes"][0]
    assert ch["payload"]["audience"] == "personal" and "text" in ch["editable"]
    assert not any(isinstance(v, (int, float)) for v in ch["payload"].values())
    done = client.post(f"/api/inputs/{inp['id']}/confirm", headers=b, json={"changes": [
        {"id": ch["id"], "selected": True, "payload": {"text": "Shorter walks please"}}]}).json()
    assert done["status"] == "applied"
    ins = next(i for i in client.get("/api/insights", headers=b).json()["items"] if i["key"] == "walking_tolerance")
    assert ins["text"] == "Shorter walks please" and ins["audience"] == "personal" and ins["status"] == "active"
    cancelled = client.post("/api/inputs", headers=a, json={"text": "I prefer quiet mornings"}).json()
    assert client.post(f"/api/inputs/{cancelled['id']}/cancel", headers=a).json()["status"] == "cancelled"
    kept = client.get("/api/inputs", headers=a).json()["items"]
    assert any(i["id"] == cancelled["id"] and i["original_text"] == "I prefer quiet mornings" for i in kept)


def test_provider_outage_preserves_input(client, a, monkeypatch):
    from curator.config import settings
    monkeypatch.setattr(settings, "interpreter_provider", "gemini")
    inp = client.post("/api/inputs", headers=a, json={"text": "Is there a BBQ event coming up?"}).json()
    assert inp["provider"] == "unavailable" and inp["degraded"] and inp["original_text"].startswith("Is there")
    assert inp["proposed_changes"][0]["type"] == "note"


def test_notification_retry_does_not_duplicate(client):
    from curator.services.notifications import queue_notification
    first = client.portal.call(queue_notification, "hh", "batch_published", "notif-key-1", "x@example.invalid", "New batch")
    second = client.portal.call(queue_notification, "hh", "batch_published", "notif-key-1", "x@example.invalid", "New batch")
    assert first["replay"] is False and second["replay"] is True and first["id"] == second["id"]
    assert first["status"] == "suppressed"


def test_demo_cannot_be_published_and_t05_batch_idempotency(client, a, auto):
    items = demo_items(client, a)
    low = next(i for i in items if i["fit_score"] < 70)
    demo_exp = items[0]["experience_id"]
    bad = client.post("/api/batches", headers=auto, json={"idempotency_key": "demo-pub-1", "local_date": "2026-10-14",
                      "slot": "morning", "status": "published", "items": [
                          {"experience_id": demo_exp, "rank": 1}, {"experience_id": low["experience_id"], "rank": 2}]})
    assert bad.status_code == 422
    detail = str(bad.json())
    assert "demo_record_not_publishable" in detail and "fit_score_below_threshold" in detail
    admin_body = {"idempotency_key": "demo-pub-admin", "local_date": "2026-10-14", "slot": "morning",
                  "status": "published", "items": [{"experience_id": demo_exp, "rank": 1}]}
    assert client.post("/api/admin/batches", headers=a, json=admin_body).status_code == 422
    c1 = client.post("/api/candidates", headers=auto, json=candidate("Test Mill", "history", idempotency_key="cand-1")).json()
    again = client.post("/api/candidates", headers=auto, json=candidate("Test Mill", "history", idempotency_key="cand-1")).json()
    assert again["idempotent_replay"] and again["experience_id"] == c1["experience_id"]
    c2 = client.post("/api/candidates", headers=auto, json=candidate("Test Smokehouse", "food")).json()
    assert c1["publication_check"]["eligible"] and c2["publication_check"]["eligible"]
    local = client.get("/api/auth/me", headers=a).json()["environment"]["local_date"]
    body = {"idempotency_key": "batch-key-1", "local_date": local, "slot": "midday", "status": "published",
            "items": [{"experience_id": c1["experience_id"], "rank": 1}, {"experience_id": c2["experience_id"], "rank": 2}]}
    first = client.post("/api/batches", headers=auto, json=body).json()
    second = client.post("/api/batches", headers=auto, json=body).json()
    assert first["idempotent_replay"] is False and second["idempotent_replay"] is True
    assert first["batch"]["id"] == second["batch"]["id"] and len(second["items"]) == 2
    today = client.get("/api/board/today", headers=a).json()
    assert today["mode"] == "live" and len(today["batches"]) == 1
    assert client.get("/api/batches/latest", headers=auto).json()["batch"]["id"] == first["batch"]["id"]


def test_t07_t08_t09_api_publication_rules(client, a, auto):
    weak = client.post("/api/candidates", headers=auto, json=candidate(
        "Weak Spot", "maker", score_components={**SCORES, "uniqueness": 5})).json()
    assert "fit_score_below_threshold" in weak["publication_check"]["errors"]
    nosrc = client.post("/api/candidates", headers=auto, json=candidate("No Source Spot", "maker", evidence=[])).json()
    assert "no_evidence_source" in nosrc["publication_check"]["errors"]
    unrev = client.post("/api/candidates", headers=auto, json=candidate(
        "Unreviewed Spot", "maker", evidence=[{**REVIEWED, "verification_status": "unverified"}])).json()
    assert "evidence_not_reviewed" in unrev["publication_check"]["errors"]
    blocked = client.post("/api/candidates", headers=auto, json=candidate("Blocked Spot", "science")).json()
    client.post("/api/exclusions", headers=a, json={"scope": "experience", "target_id": blocked["experience_id"]})
    other = client.post("/api/candidates", headers=auto, json=candidate("Other Spot", "music")).json()
    r = client.post("/api/batches", headers=auto, json={"idempotency_key": "batch-blocked", "local_date": "2026-10-15",
                    "slot": "morning", "status": "published", "items": [
                        {"experience_id": blocked["experience_id"], "rank": 1}, {"experience_id": other["experience_id"], "rank": 2}]})
    assert r.status_code == 422 and "excluded:experience" in str(r.json())


def test_t06_api_drive_through_town_not_excluded(client, auto):
    r = client.post("/api/candidates", headers=auto, json=candidate("Cambridge, Ontario", "history")).json()
    assert r["destination_matched"] is True and r["publication_check"]["eligible"], r


def test_login_lockout_and_logout_revokes(client):
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "participant.b@example.invalid", "password": "wrong"})
    r = client.post("/api/auth/login", json={"email": "participant.b@example.invalid", "password": "pytest-pass-B"})
    assert r.status_code == 429
    h = login(client, "participant.a@example.invalid", "pytest-pass-A")
    assert client.post("/api/auth/logout", headers=h).status_code == 200
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_password_reset_invalidates_sessions(client):
    h = login(client, "other@example.invalid", "other-pass")
    me = client.get("/api/auth/me", headers=h).json()
    client.portal.call(provision_member, me["household"]["id"], "other@example.invalid", "new-pass", "x", True)
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_health_exposes_no_secrets(client):
    body = client.get("/api/health").text
    assert "pytest-secret" not in body and "automation-key" not in body
