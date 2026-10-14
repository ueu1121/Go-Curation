"""Setup diagnostic. Prints check names and pass/fail only, never secret values. Exit 1 on failure."""
import asyncio
import json
import sys

from curator.db import db
from curator.migrations import run_migrations
from curator.routes.admin import setup_report


async def main() -> int:
    if "--migrate" in sys.argv:
        print("applied:", await run_migrations(db))
    report = await setup_report()
    print(json.dumps({"ok": report["ok"], "app_env": report["app_env"], "demo_mode": report["demo_mode"],
                      "checks": [{"check": c["check"], "ok": c["ok"]} for c in report["checks"]],
                      "providers": report["providers"]}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
