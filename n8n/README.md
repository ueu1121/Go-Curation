# n8n workflows

None exist or are active in Phase 1. Planned workflows (Phase 2, require owner approval and credentials):
1. `research-morning` (05:00 America/Toronto) and `research-midday` (10:00): `GET /api/curation-context` → discovery
   (Firecrawl) → extraction (Gemini, evidence-only) → `POST /api/candidates`.
2. `publish-morning` (06:30) / `publish-midday` (11:30): choose eligible candidates → `POST /api/batches`
   with `idempotency_key = auto-<local_date>-<slot>`.
3. `idea-research` (hourly): queued ideas → research → `POST /api/automation/ideas/{id}/outcome`.
4. `notify` after publish: short Gmail message linking to the board, idempotency key `notify-<batch_id>`.
All calls use the `X-Automation-Key` header stored in n8n credentials, never in workflow JSON.
