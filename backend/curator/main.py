import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .db import client, db
from .migrations import run_migrations
from .routes import admin, auth, automation, board, participant
from .seed import run_seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations(db)
    await run_seed()
    yield
    client.close()


app = FastAPI(title="Burlington Excursion Curator API", version="0.1.0-phase1", lifespan=lifespan)
for r in (auth.router, board.router, participant.router, automation.router, admin.router):
    app.include_router(r)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Automation-Key"],
)

STATIC_DIR = os.environ.get("STATIC_DIR", "")
if STATIC_DIR and Path(STATIC_DIR, "index.html").is_file():
    root = Path(STATIC_DIR).resolve()
    app.mount("/static", StaticFiles(directory=root / "static"), name="static")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        target = (root / path).resolve()
        if path and target.is_file() and root in target.parents:
            return FileResponse(target)
        return FileResponse(root / "index.html")
