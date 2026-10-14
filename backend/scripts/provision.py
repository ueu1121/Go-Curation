"""Provision or reset a participant account. Never logs the password.

Usage (from backend/):
  python -m scripts.provision --email someone@example.com --name "Participant A"
  python -m scripts.provision --email someone@example.com --name "Participant A" --reset
Password source: PROVISION_PASSWORD env var, otherwise an interactive prompt.
A reset replaces the hash and deletes every existing session for that account.
"""
import argparse
import asyncio
import getpass
import os

from curator.db import db
from curator.migrations import run_migrations
from curator.seed import ensure_household, provision_member


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--household", default="primary")
    p.add_argument("--reset", action="store_true")
    args = p.parse_args()
    password = os.environ.get("PROVISION_PASSWORD") or getpass.getpass("New password (min 12 chars): ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters")
    await run_migrations(db)
    hid = await ensure_household(args.household)
    result = await provision_member(hid, args.email, password, args.name, reset=args.reset)
    print(f"{args.email}: {result}" + (" (use --reset to change the password)" if result == "exists" else ""))


if __name__ == "__main__":
    asyncio.run(main())
