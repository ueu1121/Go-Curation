"""Request schemas (the typed API contract). Mirrored for the frontend in frontend/src/api/types.ts."""
from typing import Literal, Optional

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from .domain.validation import clean_text, clean_url

Effort = Literal["easy", "moderate", "involved"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


Txt = Annotated[Optional[str], AfterValidator(clean_text)]
Url = Annotated[Optional[str], AfterValidator(clean_url)]
Req = Annotated[str, AfterValidator(clean_text)]
ReqUrl = Annotated[str, AfterValidator(clean_url)]


class LoginIn(Strict):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=256)


class DisplayNameIn(Strict):
    display_name: Req = Field(min_length=1, max_length=40)


class ReactionIn(Strict):
    batch_item_id: str
    reaction: Literal["interested", "not_today", "not_for_us"]
    reason: Txt = Field(default=None, max_length=500)


class PlanIn(Strict):
    batch_item_id: str
    planned_date: Optional[str] = None


class VisitIn(Strict):
    plan_id: str
    visit_date: Optional[str] = None
    notes: Txt = Field(default=None, max_length=2000)


class FeedbackIn(Strict):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    notes: Txt = Field(default=None, max_length=2000)


class InterestIn(Strict):
    experience_id: str
    note: Txt = Field(default=None, max_length=200)


class IdeaIn(Strict):
    description: Req = Field(min_length=3, max_length=2000)
    url: Url = None
    location: Txt = Field(default=None, max_length=200)
    preferred_date: Optional[str] = None


class IdeaOutcomeIn(Strict):
    status: Literal["queued", "researching", "eligible", "not_selected", "needs_information", "expired"]
    reason: Txt = Field(default=None, max_length=1000)
    linked_experience_id: Optional[str] = None


class ExclusionIn(Strict):
    scope: Literal["destination", "experience", "category"]
    target_id: Optional[str] = None
    category: Txt = Field(default=None, max_length=60)
    label: Txt = Field(default=None, max_length=200)
    reason: Txt = Field(default=None, max_length=500)
    temporary: bool = False
    expires_on: Optional[str] = None


class InsightPatch(Strict):
    action: Literal["accept", "dismiss", "edit"]
    text: Txt = Field(default=None, max_length=300)


class InputIn(Strict):
    text: Req = Field(min_length=1, max_length=2000)
    url: Url = None
    context_ref: Optional[dict] = None
    modality: Literal["text"] = "text"


class ChangeEdit(Strict):
    id: str
    selected: bool = True
    payload: Optional[dict] = None


class InputConfirm(Strict):
    changes: list[ChangeEdit]


class ClarifyIn(Strict):
    choice_id: str


class DestinationIn(Strict):
    id: Optional[str] = None
    name: str = Field(min_length=2, max_length=200)
    aliases: list[str] = Field(default_factory=list, max_length=20)
    kind: str = Field(default="attraction", max_length=40)
    locality: Txt = Field(default=None, max_length=120)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)
    coordinates_verified: bool = False
    external_ids: dict[str, str] = Field(default_factory=dict)


class CostIn(Strict):
    min: Optional[float] = Field(default=None, ge=0)
    max: Optional[float] = Field(default=None, ge=0)
    currency: str = "CAD"
    status: Literal["unknown", "estimate", "verified"] = "unknown"


class BookingIn(Strict):
    required: Optional[bool] = None
    deadline: Optional[str] = None
    url: Url = None
    notes: Txt = Field(default=None, max_length=500)


class TravelIn(Strict):
    geo_distance_km: Optional[float] = Field(default=None, ge=0)
    geo_method: Txt = Field(default=None, max_length=80)
    driving_distance_km: Optional[float] = Field(default=None, ge=0)
    driving_duration_min: Optional[float] = Field(default=None, ge=0)
    measurement_source: Txt = Field(default=None, max_length=120)
    status: Literal["unknown", "estimate", "verified"] = "unknown"


class OccurrenceIn(Strict):
    start_date: str
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Literal["America/Toronto"] = "America/Toronto"
    availability_status: Literal["unknown", "available", "limited", "sold_out", "cancelled"] = "unknown"
    booking_deadline: Optional[str] = None


class EvidenceIn(Strict):
    url: ReqUrl = Field(min_length=8, max_length=2048)
    source_type: Literal["official", "news", "community", "review", "listing", "other"] = "other"
    title: Txt = Field(default=None, max_length=300)
    retrieved_at: Optional[str] = None
    supported_claim: str = Field(min_length=3, max_length=500)
    verification_status: Literal["unverified", "reviewed_supports_claim", "reviewed_partial",
                                 "reviewed_does_not_support", "stale"] = "unverified"
    excerpt: Txt = Field(default=None, max_length=500)


class ExperienceIn(Strict):
    title: str = Field(min_length=3, max_length=200)
    category: str = Field(min_length=2, max_length=60)
    kind: Literal["evergreen", "seasonal", "dated_event"]
    description: str = Field(min_length=3, max_length=2000)
    why_now: Txt = Field(default=None, max_length=500)
    why_unique: Txt = Field(default=None, max_length=1000)
    fit_explanation: Txt = Field(default=None, max_length=1000)
    hidden_perk: Txt = Field(default=None, max_length=500)
    best_timing: Txt = Field(default=None, max_length=300)
    duration_estimate: Txt = Field(default=None, max_length=100)
    suggested_window: Txt = Field(default=None, max_length=100)
    effort: Optional[Effort] = None
    indoor: Optional[bool] = None
    cost_for_two: CostIn = Field(default_factory=CostIn)
    crowd_guidance: Txt = Field(default=None, max_length=500)
    crowd_level: Optional[Literal["low", "moderate", "high"]] = None
    booking: BookingIn = Field(default_factory=BookingIn)
    accessibility_notes: Txt = Field(default=None, max_length=500)
    weather_notes: Txt = Field(default=None, max_length=500)
    nearby_backup: Txt = Field(default=None, max_length=300)
    distinct_angle: Txt = Field(default=None, max_length=500)
    novelty_explanation: Txt = Field(default=None, max_length=500)
    repeat_exception: Txt = Field(default=None, max_length=500)
    exceptional_distance: bool = False
    unknowns: list[str] = Field(default_factory=list, max_length=30)
    verification_notes: Txt = Field(default=None, max_length=1000)


class CandidateIn(Strict):
    idempotency_key: Txt = Field(default=None, max_length=200)
    linked_idea_id: Optional[str] = None
    destination: DestinationIn
    experience: ExperienceIn
    travel: TravelIn = Field(default_factory=TravelIn)
    occurrences: list[OccurrenceIn] = Field(default_factory=list, max_length=50)
    evidence: list[EvidenceIn] = Field(default_factory=list, max_length=30)
    score_components: dict[str, float]


class BatchItemIn(Strict):
    experience_id: str
    occurrence_id: Optional[str] = None
    rank: int = Field(ge=1, le=10)
    novelty_explanation: Txt = Field(default=None, max_length=500)
    repeat_exception: Txt = Field(default=None, max_length=500)


class BatchIn(Strict):
    idempotency_key: str = Field(min_length=6, max_length=200)
    local_date: str
    slot: Literal["morning", "midday"]
    status: Literal["draft", "published", "insufficient_candidates"]
    items: list[BatchItemIn] = Field(default_factory=list, max_length=5)
    note: Txt = Field(default=None, max_length=500)


class EvidenceReviewIn(Strict):
    verification_status: Literal["unverified", "reviewed_supports_claim", "reviewed_partial",
                                 "reviewed_does_not_support", "stale"]
    note: Txt = Field(default=None, max_length=500)
