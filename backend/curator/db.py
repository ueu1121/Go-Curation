import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings

client = AsyncIOMotorClient(settings.mongo_url, tz_aware=True)
db = client[settings.db_name]

TZ = ZoneInfo("America/Toronto")
NO_ID = {"_id": 0}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or utcnow()).astimezone(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def local_today(now: datetime | None = None) -> date:
    return (now or utcnow()).astimezone(TZ).date()


def end_of_local_day(d: date) -> str:
    return iso(datetime.combine(d, time(23, 59, 59), TZ))


def clean(value):
    """Defensive: drop Mongo _id keys before returning documents."""
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k != "_id"}
    return value


def local_date_offset(days: int) -> str:
    return (local_today() + timedelta(days=days)).isoformat()
