# Product specification (Phase 1)

## Purpose
A personalised local-opportunity curator for two adults (~50) from Burlington, Ontario. It should make them feel
informed without making an outing feel like work: few options, clear reasons, honest unknowns, durable memory.

## Participants and availability
- Two participants in one household; display names editable (identity is separate from name).
- Available Mon–Sun, leave ~1 PM, home by 9 PM. **An availability window, not a target to fill.**
- Distance: primary 50 km; exceptional up to 90 km only if worthwhile and labelled. Basis is configurable.
- Preferences: calm, unique, lower-crowd; nature, wildlife, history, culture, scenic drives, food, seasonal, lightly adventurous.
- Avoid: malls, bars/clubs as the main outing, theme parks, loud family centres, over-touristed spots without a
  distinct angle, elaborate multi-stop itineraries, repeated generic parks/waterfalls/conservation areas.
- Mobility, walking tolerance, budget and diet are **unspecified** until set — never inferred from age.

## Pages
| Page | Phase 1 behaviour |
|---|---|
| Today | Morning/midday batches, 2–5 cards each. Collapsed card: name, why now, category, effort, date/window, a one-line practical summary ("Not yet known: cost, travel time…"), both reactions, own reaction buttons, plan controls. "View details" reveals research fields, explicit unknowns, evidence, fit score vs evidence status. Empty and insufficient-candidate states. Refinement chips filter existing cards only. |
| Upcoming | Future dated occurrences with event dates and booking deadlines; "Save interest" (not a plan). |
| Our ideas | Submit description + optional URL/location/date; status queued/researching/eligible/not_selected/needs_information/expired, research due (48 h) and overdue flag, outcome + reason. Never discarded. |
| History | Visits (experience / town visit / drive-through / broad note; user-reported; needs confirmation; date unknown), plans (selected vs completed vs cancelled), offered options, declines and blocks. Per-participant ratings and notes. |
| Preferences | Shared profile (origin, distance basis, radii, window, effort, budget, walking, accessibility, diet, tie-break, interests, avoidances), personal settings, explicit exclusions. Last-changed attribution. |
| What the curator has learned | Confirmed preferences, temporary constraints, tentative observations; accept / edit / dismiss with reasons. |
| Admin | Setup diagnostic, status (runs, last batch, overdue ideas, integrations), real candidates with publication checks and evidence review, manual candidate form, batch publish/draft, demo reset. |

## Participant actions
- Reactions per participant: Interested / Not today / Not for us (+ optional reason). Not today never blocks; Not
  for us never auto-excludes. Blocking permanently is a separate, confirmed action.
- Shared: Select as our plan (not a booking, not completed) → Mark completed (creates a visit, optional date) →
  each participant rates 1–5 and adds notes. Cancel plan.
- "Both interested" when both are interested; a neutral disagreement banner otherwise. No automatic winner.

## Tell the curator
Text/URL input → saved verbatim → guided interpretation (intents + proposed changes) → clarification when ambiguous
→ edit (today vs ongoing, both vs just me, wording) → confirm or cancel → saved records + audit trail. Unsupported
input becomes a note. Questions are answered only from stored records. See `curation-rules.md` §Input routing.

## Unresolved user settings
- Exact home origin (address or coordinates) — currently "Burlington, ON — city centre (provisional)".
- Real participant emails and display names; production passwords.
- Walking tolerance, mobility/accessibility needs, budget, dietary needs, effort tolerance.
- Tie-break rule (currently none).
- Names of the many waterfalls, parks and the three conservation areas already visited.
- Confirmation of the "Lowville Park" and "Hidden Valley" fish-migration locations.
- Activities done in Paris, Elora, Niagara Falls and at Little Canada; visit dates.
- Distance basis for the 50/90 km rule (default straight-line).
- Notification recipients and preferred times (Phase 2).
