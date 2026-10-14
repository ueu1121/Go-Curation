# Agent handoff

## Latest entry — 2026-10-14 · Phase 1 foundation (milestones A, B, C + UI refinements)
- **Branch:** `foundation/phase-1` on `github.com/ueu1121/Go-Curation` (repository was empty; no `main` exists yet —
  the owner decides when to create/merge `main`). Foundation commit: `6e01d75`. Because the repository was empty,
  GitHub made `foundation/phase-1` the default branch; the owner may create `main` from it and switch the default.
- **Author:** E1 (Emergent agent). **Ownership:** no task currently claimed.

### What changed
- Backend (`backend/curator`): auth (bcrypt, revocable JWT cookie sessions, lockout, no sign-up), household-scoped
  participant API, automation API (`X-Automation-Key`), admin API, portable domain rules (scoring, publication,
  dedup, distance policy, guided interpreter), migrations, idempotent seed (user-reported history + demo data).
- Frontend (`frontend/src`, TypeScript): Today/Upcoming/Our ideas/History, Preferences, Learned, Admin, docked
  Tell the curator with interpretation → clarification → edit → confirm/cancel.
- UI refinements from the owner's second review: docked curator bar (no overlap, hidden while keyboard open),
  compact collapsed cards with a practical summary, walking-feedback flow with explicit outing choice and
  personal editable preference (no invented number), below-threshold label on the 59/100 demo card, inline
  error on rejected idea URLs.
- Docs, root scripts, Dockerfile, `.env.example` files, `requirements-app.txt`.

### Tests actually run (2026-10-14, Emergent preview)
- `cd backend && python -m pytest -q tests` → **33 passed** (isolated DB `curator_pytest`). Covers original tests
  1–14 and expanded criteria 5–8, 9, 10, 11, 12 (see test names `test_tNN_*`).
- `flake8` → clean. `tsc --noEmit` → clean. `REACT_APP_BACKEND_URL= yarn build` → success.
- `python -m scripts.setup_check` → all checks pass (development).
- Testing agent (iteration 1): backend 43/43 live checks, UI flows at 390×844 and 360 px passed — login A/B,
  demo labelling, details/threshold text, independent reactions, disagreement → both interested, select ≠ complete,
  completion + per-participant rating, walking flow, shared preference awaiting partner, ideas, admin candidate
  form, upcoming save. One issue (no visible error for rejected idea URL) was fixed and re-checked by screenshot.
- Test records created in the preview DB were deleted afterwards (seeded history and demo data kept).

### Still mocked / not connected
- Interpretation = guided rules (labelled). Gemini adapter is a stub that raises "not connected".
- No research, Firecrawl, n8n, Gmail, weather, maps or travel lookups. Notifications are stored as `suppressed`.
- Demo cards are synthetic and cannot be published.

### Blockers / owner input needed
- Real participant emails + production passwords; exact origin; settings listed in `product-spec.md` → Unresolved user settings.
- Decide when to create `main` from `foundation/phase-1`.
- The GitHub token shared in chat should be rotated by the owner; it is not stored in the repo.

### Deployment
Verified: Emergent preview only. Docker/Railway/Replit/Vercel: documented, not yet verified (`docs/deployment.md`).
No pending migrations beyond `0001_indexes` (auto-applied on startup).

### Provider and quota assumptions
None in use. See `docs/cost-and-quota-policy.md` before enabling anything.

### Next recommended task (Replit team)
1. Import repo on Replit, follow README, run `yarn verify` and `yarn setup:check`; deploy one canonical instance with
   `APP_ENV=production`, a fresh MongoDB, and two real accounts via `scripts/provision.py`; run `scripts/smoke.py`.
2. Enter one real researched candidate through Admin, review its evidence, publish a 2-item batch, confirm Today.
Relevant files: `docs/deployment.md`, `backend/scripts/*`, `backend/curator/routes/admin.py`, `frontend/src/pages/Admin.tsx`.

### Phase 2 (requires approval, credentials, cost review)
n8n schedules (`n8n/README.md`), Firecrawl discovery, Gemini evidence-based extraction behind
`integrations/providers.py`, idea research within 24–48 h, Gmail notifications with idempotency keys.

## Current work and ownership
| Task | Owner | Branch | Status |
|---|---|---|---|
| Phase 1 foundation | E1 | foundation/phase-1 | Done, awaiting owner review |
| Replit portability reproduction | Replit Agent | portability/replit | In progress |

## Known limitations
- Guided interpreter recognises a fixed set of phrasings; everything else becomes a note.
- Temporary constraints and confirmed preferences are recorded and shown but do not yet filter future batches
  (no automated batch generation exists in Phase 1).
- Morning/midday slots are labels; nothing is scheduled.
- Single household per automation key.
