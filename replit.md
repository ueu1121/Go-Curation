# Replit setup

This project remains a React + TypeScript frontend, a FastAPI backend, and MongoDB. Replit development is configured
to use Node 20 and Python 3.11. Do not point this workspace or its tests at production data.

## Development environment

The development environment uses `DB_NAME=curator_replit_dev`, `APP_ENV=development`, demo mode, and disabled
research, notifications, and scheduling. The two development identities are
`participant.a@example.invalid` and `participant.b@example.invalid`; their passwords are held only in Replit Secrets.
Do not publish this development configuration as a public production instance.

Required Replit Secrets:

- `MONGO_URL`: URI for an isolated development MongoDB database.
- `JWT_SECRET`: 64 hexadecimal characters.
- `AUTOMATION_API_KEY`: at least 24 random characters.
- `DEV_PARTICIPANT_A_PASSWORD` and `DEV_PARTICIPANT_B_PASSWORD`: fresh development-only passwords.

`DB_NAME`, `APP_ENV`, `DEMO_MODE`, `COOKIE_SECURE`, `ADMIN_EMAILS`, participant email names, and the disabled
provider settings are non-secret development variables. The app uses guided interpretation only; live research,
email, and scheduled publishing remain disabled.

## Install and run

Select the pinned Node version before running Yarn. In this Replit environment the Yarn executable has a Node 24
shebang even when Node 20 is selected, so invoke its script through the active Node executable:

```bash
nvm use
node "$(command -v yarn)" install:all
node "$(command -v yarn)" lint
node "$(command -v yarn)" typecheck
node "$(command -v yarn)" test
node "$(command -v yarn)" build
```

Check the database configuration and apply migrations only after confirming `DB_NAME` is isolated:

```bash
cd backend && python -m scripts.setup_check --migrate
```

The Replit workflow builds the frontend and runs FastAPI on port 5000:

```bash
nvm use && node "$(command -v yarn)" build && PORT=5000 STATIC_DIR=../frontend/build node "$(command -v yarn)" start
```

The `STATIC_DIR` path is relative to the backend working directory. FastAPI serves the built frontend and `/api` from
the same origin. Leave `REACT_APP_BACKEND_URL` empty for this arrangement; `CORS_ORIGINS` is only needed if frontend
and backend are split across origins.

## Authentication and routing

Participant sign-in uses the app's `curator_session` httpOnly cookie, `SameSite=Lax`, with a seven-day lifetime.
`COOKIE_SECURE=true` is set for the HTTPS Replit preview. The backend serves the frontend and API on one origin, so
no separate auth callback or CORS origin is needed. If a split-origin setup is used, set the frontend's
`REACT_APP_BACKEND_URL` at build time and set `CORS_ORIGINS` to the exact frontend origin on the backend.

## Setup and verification status

The app has not yet been verified running in Replit. The workspace's observed outbound IPv4 is `35.243.136.216`,
matching the temporary Atlas access-list entry reported by the user. DNS, TCP/27017, and direct TLS 1.3 with
certificate verification succeeded. The MongoDB driver then returned Atlas error `8000` (`bad auth:
authentication failed`). Setup diagnostics, migrations, tests, and smoke verification remain blocked by database
authentication; no user permissions are confirmed. The access-list entry's exact expiry is not visible from
Replit, and a changed backend egress IP may require a new entry. See `docs/project-state.md` and
`docs/troubleshooting.md`. No successful database operation or candidate outing was recorded.

When the database is reachable, smoke-test the running Replit preview with:

```bash
cd backend && BASE_URL="https://${REPLIT_DEV_DOMAIN}" python -m scripts.smoke
```

Add `SMOKE_EMAIL` and `SMOKE_PASSWORD` through the secure development environment if the smoke test should also
exercise sign-in.
