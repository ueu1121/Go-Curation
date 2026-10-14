# Data model (MongoDB, with a future Postgres mapping)

All documents use a string UUID `id`; `_id` is never returned. Timestamps are UTC ISO-8601 strings
(sessions/login locks use BSON dates for TTL). Every household-scoped collection has `household_id`.
Records carry `dataset: "real" | "demo"` where demo data could otherwise mix in.

| Collection | Key fields | Notes |
|---|---|---|
| households | id, slug, name | |
| members | id, household_id, email (unique), display_name, password_hash, active, personal_preferences | participants / household_members |
| sessions | id, member_id, expires_at (TTL) | revocable sessions |
| login_attempts | key (email), count, locked_until | throttling |
| preferences | household_id (unique), origin{label,precision,lat,lng,status}, distance_policy{basis,primary_km,exceptional_km}, availability, timezone, interests, avoidances, effort_tolerance, budget, walking_tolerance, accessibility_needs, dietary, tie_break_rule, outing_shape, change_log | unknown = "unspecified"/null |
| destinations | id, name, aliases, normalized_names, kind, locality, lat, lng, coordinates_verified, external_ids, needs_confirmation | canonical place |
| experiences | id, destination_id, title, category, kind (evergreen/seasonal/dated_event), description, why_now, why_unique, fit_explanation, hidden_perk, best_timing, duration_estimate, suggested_window, effort, indoor, cost_for_two{min,max,currency,status}, crowd_guidance, crowd_level, booking{required,deadline,url,notes}, accessibility_notes, weather_notes, nearby_backup, distinct_angle, novelty_explanation, repeat_exception, exceptional_distance, travel{geo_distance_km, geo_method, driving_distance_km, driving_duration_min, measurement_source, status}, unknowns[], verification_notes, score_components, fit_score, research_status, idempotency_key, linked_idea_id | activity at a destination |
| event_occurrences | id, experience_id, start_date, end_date, start_time, end_time, timezone, availability_status, booking_deadline | event vs occurrence |
| evidence_sources | id, experience_id, url, source_type, title, retrieved_at, supported_claim, verification_status, excerpt (≤500 chars), recorded_by, reviewed_by, reviewed_at | no full pages kept |
| batches | id, local_date, slot (morning/midday), status (draft/published/failed/insufficient_candidates/demo_preview), generated_at, published_at, idempotency_key (unique per household), note | |
| batch_items | id, batch_id, experience_id, occurrence_id, rank, snapshot, fit_score, score_components, novelty_explanation, repeat_exception | proposal history |
| reactions | member_id + batch_item_id (unique), reaction, reason, at, history[] | |
| plans | id, batch_item_id, experience_id, title, planned_date, status (selected/cancelled/completed), selected_by, visit_id | proposed ≠ selected ≠ completed |
| visits | id, destination_id, experience_id, plan_id, visit_type (experience/town_visit/drive_through/broad_note), visit_date (nullable), date_precision, user_reported, historical, needs_confirmation, notes | |
| visit_feedback | member_id + visit_id (unique), rating, notes, aspects[] | |
| user_ideas | id, submitted_by, description, url, location, preferred_date, kind, status, submitted_at, research_target_at (+24h), research_due_at (+48h), outcome{status,reason,at,by}, linked_experience_id, history[] | |
| exclusions | id, scope (destination/experience/category), target_id, category, label, reason, temporary, expires_on, active | |
| insights | id, kind (confirmed/temporary/tentative), key, value, text, audience (shared/personal), member_id, status (active/awaiting_partner/dismissed), reason, source_input_id, expires_at, history[] | learning layer |
| curator_inputs | id, member_id, original_text, url, modality, context_refs, provider, live_ai, intents, interpretation, proposed_changes, clarification, status, applied_changes, audit[] | input audit trail |
| notes | id, member_id, text, kind, source_input_id | |
| interests | member_id + experience_id (unique), note | "save for later" |
| source_registry | id, url, category, priority, last_checked, next_check_due, enabled | empty until Phase 2 |
| automation_runs | id, run_type, idempotency_key, started_at, finished_at, outcome, error_summary, usage | |
| notifications | idempotency_key (unique), kind, to, subject, status (suppressed in Phase 1) | |
| schema_migrations, seed_markers | name / key | bookkeeping |

## Future Postgres/Supabase mapping (UNVERIFIED — no SQL has been run)
Each collection maps to a table with `id uuid primary key` and `household_id uuid references households`.
Embedded objects (`travel`, `cost_for_two`, `booking`, `origin`, `distance_policy`) become columns or `jsonb`.
Arrays of strings (`aliases`, `unknowns`, `interests`) → `text[]`. `history`/`audit` arrays → child tables or `jsonb`.
Unique indexes listed above become unique constraints. Household isolation → RLS policy
`household_id = (select household_id from members where auth_user_id = auth.uid())`. Migration path: export via
the API/`mongoexport`, transform, import, then swap the repository layer in `curator/services` — domain modules
are storage-agnostic.
