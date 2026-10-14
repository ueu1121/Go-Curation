# Burlington Excursion Curator

Shared, mobile-first excursion board for two participants based in Burlington, Ontario.
**Phase 1 foundation** — demo examples and manually entered records only. No live research, AI, email or scheduling.

Agents: start with [`AGENTS.md`](AGENTS.md). Latest state: [`docs/agent-handoff.md`](docs/agent-handoff.md).

## Setup (one path)
```bash
nvm use                         # Node 20
cp backend/.env.example backend/.env      # fill MONGO_URL, DB_NAME, JWT_SECRET, AUTOMATION_API_KEY, ...
cp frontend/.env.example frontend/.env    # REACT_APP_BACKEND_URL=http://localhost:8001
yarn install:all
yarn setup:check                # add --migrate via: cd backend && python -m scripts.setup_check --migrate
yarn dev                        # http://localhost:3000
yarn verify                     # lint + typecheck + tests
```
Development accounts are created at startup only when `APP_ENV` is not `production` and
`DEV_PARTICIPANT_{A,B}_EMAIL/PASSWORD` are set in `backend/.env` (existing passwords are never overwritten).

## Accounts and password recovery (Phase 1)
- No public sign-up. Create or reset an account: `cd backend && python -m scripts.provision --email <email> --name "<name>" [--reset]`.
  The password is read from a prompt (or `PROVISION_PASSWORD`). `--reset` replaces the hash **and deletes all sessions** for that account.
- Sessions: httpOnly cookie, 7 days (`SESSION_TTL_DAYS`), server-side session record so logout/reset revoke immediately.
- Login lock: 5 failures (`LOGIN_MAX_ATTEMPTS`) → 15 minutes (`LOGIN_LOCK_MINUTES`).
- Administrators: emails listed in `ADMIN_EMAILS`.

## Deployment
See [`docs/deployment.md`](docs/deployment.md). Only the Emergent preview has been exercised; Replit, Vercel,
Railway and the Dockerfile are **documented, not yet verified**.

## Documentation
product-spec · curation-rules · data-model · integration-contract · source-strategy · cost-and-quota-policy ·
decisions · implementation-plan · deployment · agent-handoff — all in `docs/`.
