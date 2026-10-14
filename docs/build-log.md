# Build and verification log

## 2026-10-14 — Replit Atlas access recheck

### Passed

- Previously: `install:all`, lint, TypeScript typecheck, and optimized frontend build.
- Current `Start application` workflow attempt: optimized frontend build compiled successfully.
- Outbound IPv4 remained `35.243.136.216`, matching the temporary Atlas `/32` entry reported by the user.
- DNS and TCP port 27017 succeeded for all three Atlas shard nodes.
- Direct TLS to each node using the proper hostname succeeded with TLS 1.3 and normal certificate validation.

### Blocked / failed

- `python -m scripts.setup_check`: exit 1. Required/optional environment and safety checks passed; database,
  migrations, and participant-account checks failed because authenticated MongoDB access was rejected.
- MongoDB driver ping: Atlas error `8000`, `bad auth: authentication failed`.
- Workflow: frontend build passed; FastAPI startup migrations failed on the same authentication error; app exited.
- `python -m pytest -q tests`: exit 4 during `conftest.py` setup before test collection, when the fixture attempted
  database cleanup on `curator_pytest`. Authentication failed; no test database drop completed.
- `BASE_URL=https://${REPLIT_DEV_DOMAIN} python -m scripts.smoke`: failed before app checks because the HTTPS
  request failed certificate verification. The backend workflow was not serving. Verification was not weakened.

### Not verified

The authenticated user's permissions for `curator_replit_dev` and `curator_pytest`, migrations, seed/account
creation, API smoke behavior, sign-in, and signed-in UI flows remain unverified. The exact expiry of the temporary
Atlas access-list entry is not available from this workspace. A changed Replit backend egress address may require
updating the `/32` entry.
