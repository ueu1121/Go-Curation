import os
from pathlib import Path

from dotenv import load_dotenv

os.environ["DB_NAME"] = "curator_pytest"
os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["COOKIE_SECURE"] = "false"
os.environ["JWT_SECRET"] = "pytest-secret-" + "x" * 40
os.environ["AUTOMATION_API_KEY"] = "pytest-automation-key-0123456789"
os.environ["ADMIN_EMAILS"] = "participant.a@example.invalid"
os.environ["DEV_PARTICIPANT_A_EMAIL"] = "participant.a@example.invalid"
os.environ["DEV_PARTICIPANT_A_PASSWORD"] = "pytest-pass-A"
os.environ["DEV_PARTICIPANT_B_EMAIL"] = "participant.b@example.invalid"
os.environ["DEV_PARTICIPANT_B_PASSWORD"] = "pytest-pass-B"
os.environ["LOGIN_MAX_ATTEMPTS"] = "5"
os.environ["INTERPRETER_PROVIDER"] = "guided"
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pymongo import MongoClient  # noqa: E402

assert os.environ["DB_NAME"].endswith("_pytest"), "Tests must never touch a real database"
MongoClient(os.environ["MONGO_URL"]).drop_database(os.environ["DB_NAME"])

from curator.main import app  # noqa: E402

AUTO = {"X-Automation-Key": os.environ["AUTOMATION_API_KEY"]}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
    MongoClient(os.environ["MONGO_URL"]).drop_database(os.environ["DB_NAME"])


def login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.cookies.get("curator_session")
    client.cookies.clear()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def a(client):
    return login(client, "participant.a@example.invalid", "pytest-pass-A")


@pytest.fixture(scope="session")
def b(client):
    return login(client, "participant.b@example.invalid", "pytest-pass-B")


@pytest.fixture(scope="session")
def auto():
    return AUTO
