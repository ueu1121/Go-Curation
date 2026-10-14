// Typed mirror of the FastAPI contract (backend/curator/schemas.py + route responses).
export type Reaction = "interested" | "not_today" | "not_for_us";
export type Effort = "easy" | "moderate" | "involved";
export type Dataset = "demo" | "real";
export type IdeaStatus = "queued" | "researching" | "eligible" | "not_selected" | "needs_information" | "expired";
export type VerificationStatus =
  | "unverified" | "reviewed_supports_claim" | "reviewed_partial" | "reviewed_does_not_support" | "stale";

export interface Member {
  id: string; display_name: string; email: string; is_admin: boolean;
  personal_preferences: Record<string, string>;
}
export interface Me {
  member: Member; household: { id: string; name: string }; members: Member[];
  environment: { app_env: string; demo_mode: boolean; interpreter: string; live_ai: boolean;
    timezone: string; local_date: string; phase: string };
}
export interface Evidence {
  id?: string; url: string | null; source_type: string; title?: string | null; retrieved_at?: string | null;
  supported_claim: string; verification_status: VerificationStatus; excerpt?: string | null;
  reviewed_at?: string | null;
}
export interface Occurrence {
  id: string; start_date: string; end_date?: string | null; start_time?: string | null; end_time?: string | null;
  timezone: string; availability_status: string; booking_deadline?: string | null;
}
export interface Travel {
  origin_label?: string; geo_distance_km: number | null; geo_method?: string | null;
  driving_distance_km: number | null; driving_duration_min: number | null;
  measurement_source?: string | null; status: "unknown" | "estimate" | "verified";
}
export interface Cost { min: number | null; max: number | null; currency: string; status: "unknown" | "estimate" | "verified" }
export interface Experience {
  id: string; dataset: Dataset; destination_id: string; title: string; category: string;
  kind: "evergreen" | "seasonal" | "dated_event"; effort: Effort | null; indoor: boolean | null;
  description: string; why_now?: string | null; why_unique?: string | null; fit_explanation?: string | null;
  hidden_perk?: string | null; best_timing?: string | null; duration_estimate?: string | null;
  suggested_window?: string | null; cost_for_two: Cost; crowd_guidance?: string | null;
  crowd_level?: "low" | "moderate" | "high" | null;
  booking: { required: boolean | null; deadline: string | null; url?: string | null; notes: string | null };
  accessibility_notes?: string | null; weather_notes?: string | null; nearby_backup?: string | null;
  distinct_angle?: string | null; novelty_explanation?: string | null; repeat_exception?: string | null;
  travel: Travel; unknowns: string[]; verification_notes?: string | null;
  score_components: Record<string, number>; fit_score: number; evidence: Evidence[];
  occurrences: Occurrence[]; research_status: string; evidence_status?: string;
  destination?: { name: string } | null;
}
export interface ReactionRecord { member_id: string; reaction: Reaction; reason: string | null; at: string }
export interface Plan {
  id: string; batch_item_id: string; experience_id: string; title: string; planned_date: string;
  status: "selected" | "cancelled" | "completed"; selected_by: string; dataset: Dataset; visit_id?: string;
}
export interface BatchItem {
  id: string; batch_id: string; dataset: Dataset; experience_id: string; rank: number; snapshot: Experience;
  fit_score: number; score_components: Record<string, number>; novelty_explanation: string | null;
  repeat_exception: string | null; reactions: Record<string, ReactionRecord>;
  shared_state: "both_interested" | "disagreement" | "partial" | "awaiting"; plan: Plan | null; saved_by: string[];
}
export interface Batch {
  id: string; dataset: Dataset; local_date: string; slot: "morning" | "midday";
  status: "draft" | "published" | "failed" | "insufficient_candidates" | "demo_preview";
  generated_at: string; published_at: string | null; note: string | null; items: BatchItem[];
}
export interface TodayResponse { local_date: string; mode: "live" | "demo" | "empty"; batches: Batch[]; phase_notice: string }
export interface Idea {
  id: string; description: string; url: string | null; location: string | null; preferred_date: string | null;
  kind: string; status: IdeaStatus; submitted_at: string; research_target_at: string; research_due_at: string;
  outcome: { status: string; reason: string | null; at: string } | null; overdue: boolean;
  linked_experience_id: string | null; submitted_by: string;
}
export interface Visit {
  id: string; destination_name: string | null; activity: string | null; category: string | null;
  visit_type: "experience" | "town_visit" | "drive_through" | "broad_note"; visit_date: string | null;
  date_precision: string; user_reported: boolean; historical: boolean; needs_confirmation: boolean;
  notes: string | null; dataset: Dataset; plan_id: string | null;
  feedback: { member_id: string; rating?: number; notes?: string; aspects?: { aspect: string; sentiment: string }[] }[];
}
export interface Insight {
  id: string; kind: "confirmed" | "temporary" | "tentative"; key: string; value: unknown; text: string;
  audience: "shared" | "personal"; member_id: string; status: "active" | "awaiting_partner" | "dismissed";
  reason: string | null; expires_at: string | null; expired: boolean; created_at: string;
}
export interface ProposedChange {
  id: string; type: string; summary: string; payload: Record<string, any>; editable: string[]; selected: boolean;
}
export interface CuratorInput {
  id: string; original_text: string; url: string | null; provider: string; live_ai: boolean; intents: string[];
  interpretation: string; proposed_changes: ProposedChange[];
  clarification: { question: string; choices: { id: string; label: string }[]; resolved_choice?: string } | null;
  status: "needs_clarification" | "awaiting_confirmation" | "applied" | "saved_unapplied" | "cancelled";
  applied_changes: { change_id: string; type: string; result: Record<string, any> }[]; created_at: string;
}
export interface Exclusion {
  id: string; scope: "destination" | "experience" | "category"; target_id: string | null; category: string | null;
  label: string | null; reason: string | null; temporary: boolean; expires_on: string | null; active: boolean;
}
