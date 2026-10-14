"""Deployed-app smoke test. Usage: BASE_URL=https://host [SMOKE_EMAIL=.. SMOKE_PASSWORD=..] python -m scripts.smoke
Read-only: performs GET requests plus an optional login. It never writes records."""
import os
import sys

import httpx


def main() -> int:
    base = os.environ.get("BASE_URL")
    if not base:
        print("Set BASE_URL to the deployed origin")
        return 2
    with httpx.Client(base_url=base.rstrip("/"), timeout=20) as c:
        health = c.get("/api/health")
        print("health:", health.status_code, health.json().get("status"))
        ok = health.status_code == 200 and health.json().get("database") == "ok"
        ok &= c.post("/api/auth/register", json={}).status_code == 403
        ok &= c.get("/api/board/today").status_code == 401
        email, pw = os.environ.get("SMOKE_EMAIL"), os.environ.get("SMOKE_PASSWORD")
        if email and pw:
            r = c.post("/api/auth/login", json={"email": email, "password": pw})
            token = r.cookies.get("curator_session")
            board = c.get("/api/board/today", headers={"Authorization": f"Bearer {token}"})
            print("login:", r.status_code, "board:", board.status_code, board.json().get("mode"))
            ok &= r.status_code == 200 and board.status_code == 200
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
