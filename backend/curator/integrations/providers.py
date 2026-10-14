"""Provider adapters. Phase 1 ships only local/disabled implementations."""
from typing import Protocol

from ..config import settings
from ..domain.interpreter import interpret as guided_interpret


class ProviderUnavailable(Exception):
    pass


class InterpretationProvider(Protocol):
    name: str
    live: bool

    def interpret(self, text: str, url: str | None, ctx: dict) -> dict: ...


class GuidedRuleInterpreter:
    name = "guided_rules"
    live = False

    def interpret(self, text: str, url: str | None, ctx: dict) -> dict:
        return guided_interpret(text, url, ctx)


class GeminiInterpreter:
    name = "gemini"
    live = True

    def interpret(self, text: str, url: str | None, ctx: dict) -> dict:
        raise ProviderUnavailable("Gemini interpretation is a Phase 2 adapter and is not connected")


class DisabledNotifier:
    name = "disabled"
    live = False

    def send(self, to: str, subject: str, body: str) -> dict:
        return {"sent": False, "reason": "notifications_disabled_in_phase_1"}


def get_interpreter() -> InterpretationProvider:
    if settings.interpreter_provider == "gemini":
        return GeminiInterpreter()
    return GuidedRuleInterpreter()


def provider_status() -> list[dict]:
    return [
        {"name": "interpretation", "provider": settings.interpreter_provider, "connected": False,
         "mode": "guided rules (not live AI)"},
        {"name": "research", "provider": settings.research_provider, "connected": False,
         "mode": "disabled; manual candidates only"},
        {"name": "notifications", "provider": settings.notification_provider, "connected": False,
         "mode": "disabled; records only, nothing sent"},
        {"name": "scheduling", "provider": "n8n", "connected": False, "mode": "not activated"},
        {"name": "travel_and_maps", "provider": "none", "connected": False, "mode": "values shown as unknown"},
        {"name": "weather", "provider": "none", "connected": False, "mode": "not connected"},
    ]
