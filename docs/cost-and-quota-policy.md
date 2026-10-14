# Cost and quota policy

Phase 1 makes **no paid API calls**. Costs are hosting + MongoDB only.

| Service (Phase 2+) | Use | Cost assumption | Quota dependency |
|---|---|---|---|
| n8n | scheduling, orchestration | self-hosted (hosting cost) or n8n Cloud subscription | execution limits on cloud plans |
| Firecrawl | discovery / page extraction | paid credits; any free tier or trial is **not** permanent | credits per page/crawl |
| Gemini | evidence-based extraction, interpretation | per-token pricing; free tiers have rate limits and may change | RPM/TPM/day limits |
| Gmail | short notifications | Google account limits | daily send limits |
| Hosting (Railway/Replit/Vercel) | app + DB | plan-dependent; trial credits are not permanent | sleep/idle policies |

Controls to implement with Phase 2: per-run request budget, daily research budget, evidence cache by URL +
timestamp, bounded retries (max 3, exponential backoff), usage recorded in `automation_runs.usage`. When a
provider is unavailable, existing data is preserved, no fresh batch is fabricated, and the board shows a truthful
degraded state. Nothing here should be described as "free forever".
