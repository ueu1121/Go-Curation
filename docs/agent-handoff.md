# Agent handoff

## Latest entry — 2026-10-14 · Replit Atlas recheck (blocked on authentication)
- **Branch and commit:** `portability/replit` at `f360d9aa9367` before this documentation update; no merge or
  deployment. The original portability starting point is documented in the initial setup entry below.
- **Address and network:** outbound IPv4 rechecked as `35.243.136.216`, matching the temporary Atlas
  `35.243.136.216/32` entry reported by the user. DNS, TCP/27017, and direct TLS 1.3 with normal certificate
  verification succeeded for all three Atlas shard nodes. Replit development egress is dynamic; a changed IP may
  require a new `/32` entry. The exact expiry time and Atlas access-list state are not independently visible here.
- **Database:** configured app database is `curator_replit_dev`; tests override to isolated `curator_pytest`.
  Driver ping returned Atlas error `8000` (`bad auth: authentication failed`), so user permissions for both DBs
  are unverified.
- **Workflow:** restarted once after the access-list change. Frontend build passed; FastAPI exited during startup
  migrations on the authentication error. Do not restart repeatedly until `MONGO_URL` authentication is corrected.
- **Checks:** setup diagnostics failed for database, migrations, and participant accounts. Tests stopped in
  `conftest.py` before collection at the `curator_pytest` cleanup step. Smoke verification failed before API checks:
  the backend was down and HTTPS to the Replit preview failed certificate verification. No TLS bypass was used.
- **Diagnostics:** Python 3.11.14, OpenSSL 3.6.0, PyMongo 4.6.3, Motor 3.3.1, certifi 2026.7.22; default system
  CA file `/etc/ssl/certs/ca-certificates.crt`, 174 roots loaded.
- **Data and providers:** no database drop/write succeeded and no candidate outings were created. No production data
  or deployment changed. Real research, notifications, and scheduling remain disabled.
- **Next step:** correct the development MongoDB URI through Replit Secrets, verify database-user permissions for
  both isolated DB names (including test cleanup on `curator_pytest`), then rerun diagnostics, tests, restart, and
  smoke checks. See `docs/project-state.md`, `docs/troubleshooting.md`, and `docs/build-log.md`.

## Initial Replit setup — 2026-10-14 (superseded by latest entry)
- **Starting point:** imported `foundation/phase-1` at `56d10c8b39e2d8e43f4b4b62d88634493c9df731`, one Replit-settings
  commit newer than the brief's `f3e28f205137dea5ba85a34557344ea3dbe6ec23`. The newer commit changed `.replit` only.
- **Working branch:** `portability/replit`. The development environment is set to Node 20 / Python 3.11 and uses
  `curator_replit_dev`; all requested secrets are present in the development environment.
- **Workflow:** `Start application` is configured on port 5000. Its initial startup attempt failed before database
  authentication because the workspace could not complete Atlas TLS handshakes.
- **Changes:** pinned `pytest-xdist` in `requirements-app.txt`, because the documented install omitted the plugin
  required by `pytest.ini`; added `replit.md`; updated the Replit deployment status below.
- **Checks:** `install:all`, lint, TypeScript typecheck, and production build passed. Setup diagnostics report the
  database unreachable. Backend tests stop during `conftest.py` before collecting tests because Atlas TLS handshakes
  fail. Smoke tests and signed-in/manual UI flows are blocked and were not claimed as passing.
- **Data and providers:** no candidate outings were created; no real or production database records were changed.
  Interpretation remains guided, while research, notifications, and scheduling stay disabled.
- **Initial blocker:** Atlas TLS connectivity. The latest entry records that network/TLS now work, but database
  authentication is rejected. No deployment or branch merge was done.

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
| Replit portability reproduction | Replit Agent | portability/replit | Blocked on Atlas database authentication |

## Known limitations
- Guided interpreter recognises a fixed set of phrasings; everything else becomes a note.
- Temporary constraints and confirmed preferences are recorded and shown but do not yet filter future batches
  (no automated batch generation exists in Phase 1).
- Morning/midday slots are labels; nothing is scheduled.
- Single household per automation key.
