import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


def _bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def _list(name: str) -> list[str]:
    return [x.strip().lower() for x in os.environ.get(name, "").split(",") if x.strip()]


class Settings:
    def __init__(self) -> None:
        self.mongo_url = os.environ["MONGO_URL"]
        self.db_name = os.environ["DB_NAME"]
        self.jwt_secret = os.environ["JWT_SECRET"]
        self.app_env = os.environ.get("APP_ENV", "development")
        self.demo_mode = _bool("DEMO_MODE") and self.app_env != "production"
        self.session_ttl_days = int(os.environ.get("SESSION_TTL_DAYS", "7"))
        self.login_max_attempts = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "5"))
        self.login_lock_minutes = int(os.environ.get("LOGIN_LOCK_MINUTES", "15"))
        self.cookie_secure = _bool("COOKIE_SECURE", "true")
        self.admin_emails = _list("ADMIN_EMAILS")
        self.automation_key = os.environ.get("AUTOMATION_API_KEY", "")
        self.automation_household_slug = os.environ.get("AUTOMATION_HOUSEHOLD_SLUG", "primary")
        self.cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
        self.interpreter_provider = os.environ.get("INTERPRETER_PROVIDER", "guided")
        self.research_provider = os.environ.get("RESEARCH_PROVIDER", "disabled")
        self.notification_provider = os.environ.get("NOTIFICATION_PROVIDER", "disabled")

    def dev_accounts(self) -> list[dict]:
        if self.app_env == "production":
            return []
        out = []
        for slot, name in (("A", "Participant A"), ("B", "Participant B")):
            email = os.environ.get(f"DEV_PARTICIPANT_{slot}_EMAIL", "").strip().lower()
            pw = os.environ.get(f"DEV_PARTICIPANT_{slot}_PASSWORD", "")
            if email and pw:
                out.append({"email": email, "password": pw, "display_name": name})
        return out


settings = Settings()

REQUIRED_ENV = ["MONGO_URL", "DB_NAME", "JWT_SECRET", "APP_ENV"]
OPTIONAL_ENV = [
    "CORS_ORIGINS", "DEMO_MODE", "SESSION_TTL_DAYS", "LOGIN_MAX_ATTEMPTS", "LOGIN_LOCK_MINUTES",
    "COOKIE_SECURE", "ADMIN_EMAILS", "AUTOMATION_API_KEY", "AUTOMATION_HOUSEHOLD_SLUG",
    "INTERPRETER_PROVIDER", "RESEARCH_PROVIDER", "NOTIFICATION_PROVIDER", "GEMINI_API_KEY",
    "FIRECRAWL_API_KEY",
]
