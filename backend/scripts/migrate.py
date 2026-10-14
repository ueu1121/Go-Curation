"""Apply pending versioned MongoDB migrations. Usage: python -m scripts.migrate"""
import asyncio

from curator.db import db
from curator.migrations import run_migrations

if __name__ == "__main__":
    print("applied:", asyncio.run(run_migrations(db)) or "none pending")
