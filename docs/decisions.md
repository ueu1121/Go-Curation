# Architecture decisions

Status: all decisions below are **approved by the project owner** unless marked otherwise.

| ID | Decision | Status |
|---|---|---|
| D-001 | Stack: React + TypeScript frontend, FastAPI (Python 3.11) backend, MongoDB. No Next.js or Supabase in Phase 1. | Approved |
| D-002 | Authoritative domain rules live once, in Python (`backend/curator/domain`). The frontend only mirrors API types (`frontend/src/api/types.ts`); business rules are not duplicated in TypeScript. Refinement chips are client-side filters only. | Approved |
| D-003 | Persistence behind a service/repository layer (`curator/services`). A future Postgres/Supabase migration is documented in `data-model.md`; no SQL is shipped, so none is claimed verified. One active database only. | Approved |
| D-004 | Repository layout `backend/` + `frontend/` instead of `apps/web` + `packages/*`, because the environment runs these two services under supervisor. Domain modules remain provider-free and portable. | Approved (deviation recorded) |
| D-005 | Auth: portable email/password for two provisioned accounts, bcrypt hashing, JWT inside an httpOnly SameSite=Lax cookie (Bearer header also accepted), server-side session record (`sessions`) so logout and password reset revoke. 7-day expiry, 5 failures → 15-minute lock. No public sign-up. Emergent-managed auth not used. | Approved |
| D-006 | Development identities `participant.a@example.invalid` / `participant.b@example.invalid`, display names Participant A / B. Development only; disabled when `APP_ENV=production`. Passwords generated locally, stored only in git-ignored `backend/.env`, never overwritten on restart. | Approved |
| D-007 | Administrator = any account in `ADMIN_EMAILS` (dev: Participant A). No third account is created, to keep the two-participant limit. | Default |
| D-008 | Tie-break between participants: none — decide together. Configurable text in Preferences. | Approved |
| D-009 | Interpreter: deterministic guided rules, labelled "Guided interpretation — live AI not connected". Provider adapter interface ready for Gemini (Phase 2). | Approved |
| D-010 | Publication requires fit ≥ 70, ≥ 1 source with a URL **and** a reviewed verification state, no active exclusion, dedup rules, non-demo dataset. URL format checks are structural only. Manually entered candidates follow the same rules; unreviewed ones stay drafts. | Approved |
| D-011 | Distance: straight-line, driving distance and driving time stored separately with method/source/status. The 50/90 km rule applies to one configurable basis (`distance_policy.basis`, default geographic). Unknown is shown as unknown, never zero. Origin: Burlington city centre, provisional, coordinates unset. | Approved |
| D-012 | Timezone America/Toronto for local dates and display; timestamps stored as UTC ISO strings. | Approved |
| D-013 | GitHub: repository `ueu1121/Go-Curation` (was empty). Work pushed to branch `foundation/phase-1` only; no `main` created by agents; no merge without owner approval; no force-push. | Approved |
| D-014 | Production image serves the React build from FastAPI (`STATIC_DIR`) for a same-origin single deployment. Vercel (static frontend) + Railway/Replit (backend) is the documented alternative. | Default |
| D-015 | Shared ongoing preferences proposed by one participant stay `awaiting_partner` until the other accepts; personal preferences can only be changed by their owner. | Default |
| D-016 | `requirements.txt` is the Emergent environment file; `requirements-app.txt` is the pinned portable lock used by Docker/other hosts. Frontend lockfile: `frontend/yarn.lock`. | Default |
