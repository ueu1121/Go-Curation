"""Deterministic guided interpreter. Phase 1 only; it does not understand arbitrary language."""
import re
from datetime import date, timedelta

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
CATEGORY_WORDS = {
    "waterfall": "waterfall", "park": "park", "conservation area": "conservation_area",
    "mall": "shopping_mall", "museum": "museum", "winery": "winery", "wineries": "winery",
    "hike": "hike", "trail": "trail", "bar": "bar",
}
AVOID_RE = re.compile(
    r"(?:not another|no more|nothing|no|avoid|skip|without)\s+(?:\w+\s)?"
    r"(waterfalls?|parks?|conservation areas?|malls?|museums?|wineries|winery|hikes?|trails?|bars?)"
)
QUESTION_RE = re.compile(r"^(is|are|any|what|when|where|how|can|could|would|do|does)\b")


def _title(s: str) -> str:
    return " ".join(w.capitalize() for w in s.strip(" .,'").split())


def _category(word: str) -> str:
    for key, val in CATEGORY_WORDS.items():
        if word.startswith(key):
            return val
    return word


def _when(word: str | None, today: date) -> tuple[str | None, str]:
    if word == "yesterday":
        return (today - timedelta(days=1)).isoformat(), "day"
    if word == "today":
        return today.isoformat(), "day"
    return None, "unknown"


class _Builder:
    def __init__(self, text: str):
        self.text = text
        self.intents: list[str] = []
        self.changes: list[dict] = []
        self.clarification: dict | None = None

    def add(self, intent: str, type_: str, summary: str, payload: dict, editable=None, selected=True):
        if intent not in self.intents:
            self.intents.append(intent)
        self.changes.append({
            "id": f"c{len(self.changes) + 1}", "type": type_, "summary": summary,
            "payload": payload, "editable": editable or [], "selected": selected,
        })

    def ask(self, intent: str, question: str, choices: list[dict]):
        if intent not in self.intents:
            self.intents.append(intent)
        choices.append({"id": "note_only", "label": "Just keep this as a note",
                        "changes": [{"type": "note", "summary": "Save as a note", "payload": {"text": self.text}}]})
        self.clarification = {"question": question, "choices": choices}


def _links(b: _Builder, text: str, url: str | None):
    urls = URL_RE.findall(text) + ([url] if url else [])
    if urls:
        b.add("event_lead", "create_idea",
              "Queue this link as an idea to research. The link has not been checked or verified.",
              {"description": text or "Shared link", "url": urls[0], "kind": "event_lead"})
    return bool(urls)


def _drive_through(b: _Builder, t: str) -> bool:
    m = re.search(r"\bdr(?:ove|ive|iving) (?:through|thru|past) ([a-z .'-]+?)(?:,| but| and|\.|$)", t)
    if not m:
        return False
    place = _title(m.group(1))
    b.add("historical_visit", "historical_visit",
          f"Record a drive-through of {place}. It does not count as visiting attractions there and "
          f"will not block future ideas in {place}.",
          {"place": place, "visit_type": "drive_through", "visit_date": None, "date_precision": "unknown"})
    return True


def _went(b: _Builder, t: str, ctx: dict):
    m = re.search(r"\bwe (?:went|visited|were at|got to)\s+(?:to\s+)?(.+?)"
                  r"(?:\s+(yesterday|today|last week|last weekend))?(?:[.,!]|$)", t)
    if not m:
        return
    target, when = m.group(1).strip(), m.group(2)
    visit_date, precision = _when(when, ctx["today"])
    choices = []
    plan = ctx.get("selected_plan")
    if plan:
        choices.append({"id": "complete_plan", "label": f"We completed our plan: {plan['title']}",
                        "changes": [{"type": "complete_plan", "summary": f"Mark '{plan['title']}' completed",
                                     "payload": {"plan_id": plan["id"], "visit_date": visit_date,
                                                 "date_precision": precision}}]})
    if target not in ("there", "it", "that", "that place"):
        place = _title(target)
        choices.append({"id": "separate_visit", "label": f"Record a separate visit to {place}",
                        "changes": [{"type": "historical_visit", "summary": f"Record a visit to {place}",
                                     "payload": {"place": place, "visit_type": "experience",
                                                 "visit_date": visit_date, "date_precision": precision}}]})
    b.ask("completion", "Which visit should this be recorded against?", choices)


def _walking(b: _Builder, t: str, ctx: dict) -> bool:
    if not re.search(r"too much walking|walking was too much|too far to walk|too much (?:of a )?walk", t):
        return False
    visits = ctx.get("recent_visits") or ([ctx["last_visit"]] if ctx.get("last_visit") else [])
    choices = []
    for v in visits[:3]:
        label = f"This was about an outing: {v['title']}" + (" (demo)" if v.get("is_demo") else "")
        choices.append({"id": f"about_visit_{v['id'][:8]}", "label": label,
                        "changes": [{"type": "visit_feedback", "summary": f"Feedback on '{v['title']}': walking was too much",
                                     "payload": {"visit_id": v["id"], "aspect": "walking", "sentiment": "negative"}}]})
    if not visits:
        choices.append({"id": "about_unrecorded_outing", "label": "This was about an outing (not recorded on the board yet)",
                        "changes": [{"type": "note", "summary": "Save as outing feedback to attach once the visit is recorded",
                                     "payload": {"text": b.text, "kind": "outing_feedback"}}]})
    choices.append({"id": "future_limit", "label": "Use less walking for my future suggestions",
                    "changes": [{"type": "set_preference",
                                 "summary": "Prefer less walking in future suggestions (no distance limit is assumed)",
                                 "payload": {"key": "walking_tolerance", "value": "less than this outing",
                                             "text": "Prefer less walking than this outing",
                                             "audience": "personal", "scope": "permanent"},
                                 "editable": ["text", "scope", "audience"]}]})
    question = "Was this about an outing you completed, or should I use less walking for future suggestions?"
    if len(visits) > 1:
        question = "Which outing was this about — or is it a preference for future suggestions?"
    b.ask("feedback_or_preference", question, choices)
    return True


def _crowd(b: _Builder, t: str, ctx: dict) -> bool:
    if not ("crowd" in t and re.search(r"lik|nice|enjoy|good|great|lovely", t)):
        return False
    lv = ctx.get("last_visit")
    if not lv:
        b.ask("feedback", "Which outing was this about? I could not find a completed outing to attach it to.", [])
        return True
    b.add("feedback", "visit_feedback", f"Note on '{lv['title']}': liked the experience, not the crowd",
          {"visit_id": lv["id"], "aspect": "crowd", "sentiment": "negative", "liked_overall": True})
    if not lv.get("is_demo"):
        b.add("tentative_observation", "tentative_observation",
              "Tentative observation: crowd level may matter more than the destination itself",
              {"text": "Crowd level may matter more than the destination", "key": "crowd_sensitivity",
               "reason": f"Feedback on '{lv['title']}'"})
    return True


def _constraints(b: _Builder, t: str):
    m = AVOID_RE.search(t)
    if m:
        cat = _category(m.group(1))
        b.add("temporary_constraint", "set_constraint", f"Skip {cat.replace('_', ' ')} suggestions",
              {"key": "avoid_category", "value": cat, "scope": "today", "audience": "shared"},
              editable=["scope", "audience"])
    if re.search(r"\b(easy|easier|low[- ]effort|relaxed|gentle)\b", t):
        b.add("temporary_constraint", "set_constraint", "Keep effort easy",
              {"key": "effort_max", "value": "easy", "scope": "today", "audience": "shared"},
              editable=["scope", "audience"])
    if re.search(r"nothing expensive|not expensive|\bcheap\b|low[- ]cost|inexpensive|\bfree\b|on a budget", t):
        b.add("temporary_constraint", "set_constraint", "Keep cost low",
              {"key": "budget", "value": "low", "scope": "today", "audience": "shared"},
              editable=["scope", "audience"])
    if re.search(r"\bindoors?\b|\binside\b", t):
        b.add("temporary_constraint", "set_constraint", "Prefer indoor options",
              {"key": "indoor", "value": True, "scope": "today", "audience": "shared"},
              editable=["scope", "audience"])


def _shape_and_prefs(b: _Builder, t: str):
    if re.search(r"one (?:main )?stop|single stop|food nearby|maybe food", t):
        b.add("preference", "set_preference", "Prefer one main stop, with food nearby optional",
              {"key": "outing_shape", "value": "one main stop, optional food nearby",
               "text": "One main stop, optional food nearby", "scope": "permanent", "audience": "shared"},
              editable=["scope", "audience"])
        return
    m = re.search(r"\b(i|we) (prefer|like|love|enjoy|don't like|do not like|dislike|hate)\b (.+)", t)
    if m and not b.changes:
        who, verb, what = m.groups()
        negative = verb in ("don't like", "do not like", "dislike", "hate")
        b.add("preference", "set_preference", f"{'Avoid' if negative else 'Favour'}: {what.strip(' .')}",
              {"key": "note", "value": what.strip(" ."), "text": f"{verb} {what.strip(' .')}",
               "sentiment": "negative" if negative else "positive", "scope": "permanent",
               "audience": "personal" if who == "i" else "shared"},
              editable=["scope", "audience"])


def _save_and_rating(b: _Builder, t: str, ctx: dict):
    m = re.search(r"\bsave (?:this|it|that)\b(?: for)?\s*(next month|next week|later|the fall|the summer)?", t)
    if m:
        focus = ctx.get("focus_item")
        if focus:
            b.add("save_for_later", "save_interest", f"Save '{focus['title']}' for {m.group(1) or 'later'}",
                  {"experience_id": focus["experience_id"], "note": m.group(1) or "later"})
        else:
            b.ask("save_for_later", "Which option should I save? Open a card and use its Save button, "
                  "or keep this as a note.", [])
    r = re.search(r"\b([1-5])\s*(?:/\s*5|stars?|out of 5)", t)
    if r:
        lv = ctx.get("last_visit")
        if lv:
            b.add("rating", "visit_rating", f"Rate '{lv['title']}' {r.group(1)}/5",
                  {"visit_id": lv["id"], "rating": int(r.group(1))})
        else:
            b.ask("rating", "Which completed outing is this rating for?", [])


def interpret(text: str, url: str | None, ctx: dict) -> dict:
    t = text.lower().strip()
    b = _Builder(text)
    has_link = _links(b, text, url)
    if not _drive_through(b, t):
        _went(b, t, ctx)
    _walking(b, t, ctx) or _crowd(b, t, ctx)
    _constraints(b, t)
    _save_and_rating(b, t, ctx)
    _shape_and_prefs(b, t)
    if not has_link and (t.endswith("?") or QUESTION_RE.match(t)):
        b.add("question", "answer_question", "Answer from records already stored (no live search in Phase 1)",
              {"query": t})
        b.add("research_request", "create_idea", "Also queue a research request for the curator",
              {"description": text, "kind": "research_request"}, selected=False)
    if re.match(r"^(actually|correction|that's wrong|that is wrong)\b", t):
        b.add("correction", "note", "Save as a correction note for review", {"text": text, "kind": "correction"})
    if not b.changes and not b.clarification:
        b.add("general_note", "note", "Keep this as a general note for the curator", {"text": text})
    return {
        "provider": "guided_rules",
        "live_ai": False,
        "intents": b.intents,
        "interpretation": "Guided interpretation: " + ", ".join(i.replace("_", " ") for i in b.intents),
        "proposed_changes": b.changes,
        "clarification": b.clarification,
    }
