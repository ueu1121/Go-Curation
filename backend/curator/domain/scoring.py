WEIGHTS = {
    "uniqueness": 25,
    "low_crowd": 20,
    "preference_fit": 15,
    "timing": 15,
    "evidence": 15,
    "practicality": 10,
}
PUBLISH_THRESHOLD = 70
VERIFIED_STATES = {"reviewed_supports_claim"}
EVIDENCE_STATES = [
    "unverified", "reviewed_supports_claim", "reviewed_partial",
    "reviewed_does_not_support", "stale",
]


def compute_fit_score(components: dict) -> tuple[float, list[str]]:
    errors: list[str] = []
    total = 0.0
    for key, weight in WEIGHTS.items():
        value = components.get(key)
        if value is None:
            errors.append(f"missing_component:{key}")
        elif not 0 <= value <= weight:
            errors.append(f"component_out_of_range:{key}")
        else:
            total += value
    for key in set(components) - set(WEIGHTS):
        errors.append(f"unknown_component:{key}")
    return round(total, 1), errors


def evidence_status(sources: list[dict]) -> str:
    """Structural summary only; a URL alone is never proof of a claim."""
    with_url = [s for s in sources if s.get("url")]
    if not with_url:
        return "none"
    states = {s.get("verification_status", "unverified") for s in with_url}
    if states <= VERIFIED_STATES:
        return "reviewed"
    if states & VERIFIED_STATES:
        return "partially_reviewed"
    return "unreviewed"
