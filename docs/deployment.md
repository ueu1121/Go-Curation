# Deployment

One canonical production app + one database. Preview/test environments must use a different `DB_NAME`
(and ideally a different cluster) and must never point at production. Status of every target:

| Target | Status |
|---|---|
| Emergent preview (supervisor: backend :8001, frontend :3000, ingress `/api` → backend) | **Verified** (dev/demo only) |
| Docker single container (`Dockerfile`) | Documented, not yet verified |
| Railway | Documented, not yet verified |
| Replit | Documented, not yet verified |
| Vercel (frontend only) | Documented, not yet verified |

## Canonical proposal
Railway (or Replit Deployments) running the Dockerfile: FastAPI serves the built React app from `STATIC_DIR`
(same origin, no CORS), plus MongoDB Atlas. `APP_ENV=production` disables demo mode and dev accounts.

## Common steps
1. Provision MongoDB; set `MONGO_URL`, `DB_NAME`.
2. Set `JWT_SECRET` (64 hex), `AUTOMATION_API_KEY`, `ADMIN_EMAILS`, `APP_ENV=production`, `COOKIE_SECURE=true`,
   `CORS_ORIGINS=<public origin>` (only needed when frontend and backend are on different origins).
3. `python -m scripts.setup_check --migrate` (from `backend/`).
4. Create the two real accounts: `python -m scripts.provision --email … --name …` (password via prompt).
5. Smoke: `BASE_URL=https://<host> python -m scripts.smoke`.
No hostname is hard-coded; the frontend uses `REACT_APP_BACKEND_URL` (empty = same origin).

## Railway
Deploy from GitHub with the Dockerfile; Railway injects `PORT`. Add variables above. Health check path `/api/health`.

## Replit
Import the repo. Run: `yarn install:all && yarn build && STATIC_DIR=../frontend/build yarn start`. Store
variables in Replit Secrets. Use a separate DB for the workspace vs the deployment.

## Vercel (frontend) + separate backend
Root `frontend/`, build `yarn build`, output `build/`, `REACT_APP_BACKEND_URL=https://<backend>`. Add a rewrite
of `/*` → `/index.html`. Backend on Railway/Replit with `CORS_ORIGINS=https://<vercel-domain>`. Cross-site cookies
require `SameSite=None`; prefer the same-origin option or a custom domain with both on subdomains.

## Auth callback URLs / allowed origins
Email/password has no OAuth callbacks. Allowed origins = `CORS_ORIGINS`. If Google sign-in is added later,
register `<origin>/auth/callback` per environment.
