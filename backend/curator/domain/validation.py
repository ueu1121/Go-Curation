import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(value: str | None, max_len: int = 2000) -> str | None:
    if value is None:
        return None
    value = _CTRL.sub("", unicodedata.normalize("NFC", str(value))).strip()
    return value[:max_len] if value else None


def clean_url(value: str | None) -> str | None:
    """Structural URL validation only. Never implies the page supports any claim."""
    if value is None or not str(value).strip():
        return None
    raw = str(value).strip()
    if len(raw) > 2048 or re.search(r"\s", raw):
        raise ValueError("URL must not contain spaces and must be under 2048 characters")
    parts = urlsplit(raw)
    if parts.scheme.lower() not in ("http", "https"):
        raise ValueError("Only http and https URLs are accepted")
    if not parts.hostname or "." not in parts.hostname:
        raise ValueError("URL must include a valid host")
    if parts.username or parts.password:
        raise ValueError("URLs with embedded credentials are not accepted")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


_STOP = {"the", "a", "an", "of", "on", "ontario", "ont", "canada", "ca"}


def normalize_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(w for w in text.split() if w not in _STOP)
