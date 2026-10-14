# Integration contract (automation + participant API)

Base path `/api`. Interactive OpenAPI: `GET /docs` on the backend. Typed mirror: `frontend/src/api/types.ts`;
request schemas: `backend/curator/schemas.py` (extra fields are rejected).

## Authentication
| Caller | Mechanism | Household |
|---|---|---|
| Participant | `POST /api/auth/login` → httpOnly cookie `curator_session` (or `Authorization: Bearer <same token>`) | from session |
| Automation (n8n) | header `X-Automation-Key: <AUTOMATION_API_KEY>` | `AUTOMATION_HOUSEHOLD_SLUG` |
| Admin | participant session whose email is in `ADMIN_EMAILS` | from session |
There is no unauthenticated write endpoint. Participant sessions are rejected on automation routes.

## Automation endpoints
### GET /api/curation-context
Returns `{untrusted_content_notice, local_date, timezone, preferences, insights, exclusions, visits (real, all time),
recent_proposals (60 days), feedback, reactions (real items), queued_ideas, upcoming_candidates}`. Demo data excluded.

### POST /api/candidates
```json
{
  "idempotency_key": "firecrawl-2026-10-14-abc",
  "linked_idea_id": null,
  "destination": {"name": "…", "aliases": [], "kind": "attraction", "locality": "…", "lat": null, "lng": null,
                  "coordinates_verified": false, "external_ids": {}},
  "experience": {"title": "…", "category": "food", "kind": "dated_event", "description": "…", "why_now": "…",
                 "effort": "easy", "cost_for_two": {"min": null, "max": null, "currency": "CAD", "status": "unknown"},
                 "booking": {"required": null, "deadline": null}, "unknowns": ["parking"], "distinct_angle": null,
                 "novelty_explanation": null, "exceptional_distance": false},
  "travel": {"geo_distance_km": null, "driving_distance_km": null, "driving_duration_min": null,
             "measurement_source": null, "status": "unknown"},
  "occurrences": [{"start_date": "2026-11-07", "end_date": null, "timezone": "America/Toronto",
                   "availability_status": "unknown", "booking_deadline": null}],
  "evidence": [{"url": "https://…", "source_type": "official", "supported_claim": "Event runs Nov 7",
                "verification_status": "unverified", "retrieved_at": "2026-10-14T10:00:00Z", "excerpt": null}],
  "score_components": {"uniqueness": 20, "low_crowd": 14, "preference_fit": 12, "timing": 13, "evidence": 10, "practicality": 7}
}
```
Response: `{experience_id, destination_id, destination_matched, fit_score, evidence_status, publication_check:
{eligible, errors[], warnings[]}, idempotent_replay, note}`. 422 on invalid scores/fields/URLs. Repeating an
`idempotency_key` returns the stored record (`idempotent_replay: true`).

### POST /api/batches (idempotent)
`{idempotency_key (required), local_date, slot: morning|midday, status: draft|published|insufficient_candidates,
items: [{experience_id, occurrence_id?, rank, novelty_explanation?, repeat_exception?}], note?}`.
`published` → all hard rules enforced; failure = 422 `{message, validation}` and nothing stored (run recorded).
`draft` → stored with validation report. `insufficient_candidates` requires `note`. Same key → same batch.

### GET /api/batches/latest
Participant or automation. `{batch|null, items[]}` — latest real published batch.

### POST /api/automation/ideas/{id}/outcome
`{status, reason?, linked_experience_id?}`; reason required for not_selected / needs_information / expired.

## Participant endpoints
| Method | Path | Body |
|---|---|---|
| GET | /api/auth/me | — |
| POST | /api/auth/logout | — |
| GET | /api/board/today | — → `{local_date, mode: live|demo|empty, batches[], phase_notice}` |
| POST | /api/reactions | `{batch_item_id, reaction: interested|not_today|not_for_us, reason?}` |
| POST | /api/plans | `{batch_item_id, planned_date?}` → plan `selected` |
| POST | /api/plans/{id}/cancel | — |
| POST | /api/visits | `{plan_id, visit_date?, notes?}` → completes plan, creates visit |
| POST | /api/visits/{id}/feedback | `{rating 1–5?, notes?}` per participant |
| POST | /api/interests | `{experience_id}` toggle save |
| GET | /api/upcoming, /api/history, /api/ideas, /api/insights, /api/exclusions, /api/preferences, /api/inputs | — |
| POST | /api/ideas | `{description, url?, location?, preferred_date?}` |
| POST | /api/inputs | `{text, url?, context_ref?: {batch_item_id}, modality: "text"}` |
| POST | /api/inputs/{id}/clarify · /confirm · /cancel | `{choice_id}` · `{changes: [{id, selected, payload?: {scope, audience, text}}]}` · — |
| PUT | /api/preferences, /api/preferences/personal, /api/members/me | partial profile · personal fields · `{display_name}` |
| POST/DELETE | /api/exclusions, /api/exclusions/{id} | `{scope, target_id?, category?, label?, reason?, temporary, expires_on?}` |
| PATCH | /api/insights/{id} | `{action: accept|dismiss|edit, text?}` |
Admin: `GET /api/admin/setup-check`, `GET /api/admin/status`, `GET|POST /api/admin/candidates`,
`PATCH /api/admin/evidence/{id}`, `POST /api/admin/batches`, `PATCH /api/admin/ideas/{id}`, `POST /api/admin/demo/reset`.
Health (public, no secrets): `GET /api/health`.

## Future modalities
`InputIn.modality` is `"text"` only. Image/voice/file will add values and an attachment reference; the stored
input record and confirmation flow stay the same. Not implemented.

## Schedule (Phase 2, not active)
n8n research runs before 06:30 and 11:30 America/Toronto; publish by 06:30 / 11:30 (ready before 06:45 / 11:45)
using `POST /api/batches` with keys like `auto-<date>-morning`. Retries reuse the key. Notifications use
`notifications.idempotency_key` (`notify-<batch_id>`), so retries never send twice.
