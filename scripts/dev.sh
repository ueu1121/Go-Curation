#!/usr/bin/env bash
# Local development: backend on :8001, frontend on :3000. Requires backend/.env and frontend/.env.
set -euo pipefail
cd "$(dirname "$0")/.."
(cd backend && uvicorn server:app --reload --host 0.0.0.0 --port 8001) &
BACK=$!
trap 'kill $BACK' EXIT
cd frontend && yarn start
