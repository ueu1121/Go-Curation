# Burlington Excursion Curator — Phase 1 Foundation Plan

A shared, mobile-first excursion board for two adults based in Burlington, Ontario. It shows a small set of timely, unusual outing options, keeps each person's reaction separate, and remembers what was proposed, selected, rejected and completed.
Phase 1 delivers the working board, persistent records, a guided "Tell the curator" inbox and a documented contract for future n8n / Firecrawl / Gemini automation. No live research, publishing, email or AI runs in this phase.

## Who it's for
- Two participants in one household (shown as "Participant A" and "Participant B"; names can be edited). Both are equal: neither can silently overwrite the other's preferences.
- An administrator/setup role (one of the participants or a developer) who provisions accounts, checks configuration and views system status.
- Future coding agents (Neo, Replit, Vercel/Railway agents, local developers) who continue from the GitHub repository without needing this chat.

## Agreed decisions (from the intake)
1. Stack: build the working app on React (TypeScript) + Python/FastAPI + MongoDB. No Next.js or Supabase build in Phase 1. Curation rules and validation live once, in Python. The frontend uses TypeScript API types generated from the OpenAPI contract. A document maps MongoDB collections to a possible future Postgres/Supabase model. Any SQL shipped is labelled "untested". Only one active database.
2. Sign-in: email + password for exactly two provisioned accounts. Public sign-up is blocked on the server, not just hidden. Passwords are hashed. Login is rate-limited, sessions expire, and logout works. No real emails or passwords are invented or committed. Preview uses separate, clearly labelled demo identities that are disabled in production. Production setup stays blocked until the two real accounts are created through a setup command.
3. Tell the curator: a rule-based guided interpreter, labelled "Guided interpretation — live AI not connected". Real input is saved as real records. A pluggable interpretation-provider interface is built now so Gemini can be added in Phase 2 without changing the UI or stored records. No AI key or gateway is turned on.
4. Display names: "Participant A" and "Participant B", editable. Identity is separate from the display name, so renaming keeps all votes, feedback and history.

## Core features and experience

### Today
- Morning and midday batches with 2–5 short cards each.
- Each card shows: name, why it's worth doing now, category, date or availability, effort (easy/moderate/involved), approximate cost for two (or "unknown"), travel info (or "unknown"), crowd guidance (or "unknown"), and both participants' reactions.
- Expanding a card shows: why it's unique, why it fits, a hidden perk, best timing, expected duration, suggested outing window, booking requirements and deadline, accessibility and walking notes, weather, an optional nearby backup, evidence links with the claim each one supports, when facts were last checked, unknowns and caveats, and how it differs from a past visit (when relevant).
- Fit score and evidence status are shown separately.
- Per-person reactions: Interested / Not today / Not for us (optional reason). Blocking something permanently is a separate action.
- Shared state: "Both interested", a neutral disagreement view comparing options against stated constraints (no automatic winner), Select as our plan, Cancel plan, Mark completed, Rate 1–5, Notes.
- Refinement chips: Easier, Quieter, Less driving, Lower cost, Indoors, More unusual, Another option. These filter the current session only, unless "Save this preference" is used. In Phase 1 they only filter or re-rank existing cards and never generate new ones.
- A friendly empty state when no batch exists, and an honest "insufficient candidates" state.

### Upcoming
- Future-dated opportunities with event dates and booking deadlines.
- "Save for later" interest, kept separate from selected or completed.

### Our ideas
- Submit a description with an optional URL, location and preferred date.
- Status tracking: queued, researching, eligible, not_selected, needs_information, expired. Each shows its research due time (24–48 h), whether it's overdue, and the outcome with a reason. Ideas are never discarded silently.

### History
- Previously offered options, selected plans, completed visits, ratings and notes, rejections and exclusions. "Selected" and "Completed" are always distinguished.
- Seeded with the user-supplied historical records (Lowville Park and Hidden Valley fish migrations, both flagged "location needs confirmation"; Little Canada; town visits to Paris, Elora and Niagara Falls; drive-throughs of Milton, Cambridge and Caledonia; broad notes on many waterfalls, many parks and three conservation areas). All dates are left unknown and every record is marked user-reported.

### Tell the curator (shared input, available from every page)
- Free text or a URL in natural phrasing. No commands to memorise.
- Flow: save the original wording → detect one or more intents (new idea, event lead, preference, today-only constraint, historical visit, reaction, completion, rating, correction, question, research request, general note) → show the proposed changes → ask one focused question if something is unclear → let the user edit, confirm or cancel → show what was saved → keep an audit trail.
- It separates personal vs shared preferences, today-only vs permanent, town visit vs attraction completed, selected vs attended, and "disliked the crowd" vs "disliked the place".
- Input it can't match is kept as a note or a clarification request.
- Questions such as "Is there a BBQ event coming up?" are answered only from stored records. If nothing is stored, it says so and offers to queue a research request.

### Preferences (secondary navigation)
- Shared profile: Burlington origin (city-level, labelled provisional), 50 km primary and 90 km exceptional radius, Mon–Sun 1 PM–9 PM window (an availability window, not a target), America/Toronto timezone, interests, avoidances and effort tolerance.
- Budget, walking tolerance and accessibility start as "Unspecified".
- Already-done records and explicit exclusions (destination / experience / category; temporary with expiry, or indefinite).
- Personal preferences per participant, attributed to that person.

### What the curator has learned (secondary navigation)
- Confirmed preferences, temporary constraints and tentative observations, each with the reasons or feedback behind it.
- Accept, edit or dismiss each one. A single negative reaction never becomes a lasting rule.

### Admin status and setup (secondary navigation, signed-in only)
- Setup diagnostic: required environment variable names (never their values), database connectivity, auth configuration, and which integrations are connected vs simulated.
- Status: last research run, last published batch, overdue ideas, unavailable integrations and failed tasks.

### Automation contract (for Phase 2, built and tested now with demo data)
- Endpoints: curation context, candidate ingestion, idempotent batch creation (draft or published), latest batch, ideas, reactions, plans and visits. Participant tokens and automation API keys are kept separate. No unauthenticated writes.
- Publishing rules enforced on the server: fit score ≥ 70 (weights: uniqueness 25, low crowd 20, preference fit 15, timing 15, evidence 15, practicality 10); at least one genuine source URL; no exclusion conflicts; the same destination not proposed within 60 days unless a stored explanation says how this experience differs (completed history is never forgotten); destinations matched by canonical identity and aliases, not only by display name; 2–5 items, aiming for at least two categories; demo records can never be published as genuine.
- Distance is stored as separate fields: straight-line distance, driving distance, driving time, measurement source, and estimate/verified status.
- Notification records include idempotency keys so a retry cannot send twice. No emails are actually sent.

### Demo mode
- Synthetic example cards, labelled "Demo example — not a real recommendation" on every card, with no realistic-looking source links. Stored separately from real records and switchable off.

## User flow
1. A participant signs in on their phone and lands on Today.
2. They browse the demo morning batch, expand a card and tap Interested. The other participant does the same on their own phone, and the board shows "Both interested" or the disagreement view.
3. Either participant taps "Select as our plan". History shows it as Selected, not Completed.
4. After the outing they tap "Mark completed", rate it 1–5 and add notes. These are kept per participant.
5. Either participant submits an idea in Our ideas or types into Tell the curator ("We drove through Cambridge, but didn't visit attractions"). They review the proposed interpretation, confirm it, and see it saved.
6. Changes persist across devices and reloads.

## UI/UX feel
- A calm, warm local concierge: restrained palette, clear typography, generous spacing and progressive disclosure, with nothing decorative.
- Mobile-first with large touch targets, a bottom tab bar (Today, Upcoming, Our ideas, History) and secondary items in a menu.
- Accessible contrast, keyboard-friendly controls and clear selected states.
- Proper loading, empty, error and offline/read-only states.
- Honest labels throughout: "unknown", "estimate", "demo", "guided interpretation".

## Implementation phases

### Phase 1 — Foundation MVP (built now)
- Everything listed under Core features, running with persistent MongoDB storage, two-account auth, demo mode, the seeded history, the guided interpreter with a provider interface, and server-side curation rules and the automation API.
- Repository portability: AGENTS.md, README with one setup path, the docs set (product spec, curation rules, data model + MongoDB→Postgres mapping, integration contract, source strategy, cost and quota policy, agent handoff, decisions), pinned dependencies and lockfiles, a backend Dockerfile, an environment example with placeholders only, a health endpoint, a setup check command, standard commands (dev, build, start, lint, typecheck, test, test:e2e, verify, setup:check), and portable JSON export/import.
- Deployment guides for Replit, Railway and Vercel (frontend), all labelled "documented, not yet verified". Only the preview here is verified.
- Tests covering the 14 original acceptance tests plus the relevant expanded criteria. Results are recorded in the handoff.

### Phase 2 — Live research and AI (not built now)
- Gemini interpretation provider behind the existing interface, still asking for confirmation on consequential changes.
- n8n scheduling for research before the 6:30 AM and 11:30 AM publications, Firecrawl discovery and extraction, evidence-based candidate curation, idea research within 24–48 h, and short Gmail notifications that link to the board.
- Requires explicit approval, credentials and a cost review first.

### Phase 3 — Refinement (not built now)
- Learned-preference suggestions drawn from accumulated feedback, an optional comparison map, image/voice/file input, optional Google sign-in on the same identity model, and an optional move to Postgres/Supabase if it proves worthwhile.

## Assumptions (decided without asking)
- Origin is "Burlington, ON (city centre, provisional)". All travel figures stay "unknown" until a real origin and measurement are provided.
- Tie-break rule between participants is "none — decide together" until both agree on one in Preferences.
- Demo identities exist only in preview. In production, both accounts are created with a setup command, and password recovery is an admin reset documented in the README (no reset emails in Phase 1).
- Sessions expire after 7 days. Login locks for 15 minutes after 5 failed attempts.
- The household is derived from the signed-in account and never from a browser-supplied ID.
- Synthetic demo cards are visually distinct from real ones and kept in a separate demo data set that the publish rules reject.
- "Not for us" reasons are stored as feedback and may only produce a tentative observation, never an automatic exclusion.
- Morning/midday batch labels follow America/Toronto local time. All timestamps are stored in UTC and displayed in Toronto time.
- No map, weather feed or travel-time API in Phase 1. Those fields are shown as entered or "unknown".
- Google Docs is not used in Phase 1.
- GitHub: work is pushed by the agent to branch `foundation/phase-1` of `ueu1121/Go-Curation` (repository was empty). No `main` is created or overwritten by agents, nothing is merged without owner approval, no force-push, no new repositories.

## Owner clarifications applied (2026-10-14)
1. Phase 1 is a foundation: live research, Gemini, email, weather, maps, travel lookups and scheduled publishing stay off; the app says so on Today and in Admin.
2. This file is the maintained plan inside the repository (copied from the workspace plan).
3. Real manual candidate path: Admin → "Enter a researched candidate" uses the same ingestion service and publication rules as `POST /api/candidates`; unreviewed evidence keeps it a draft.
4. Distance: straight-line, driving distance and driving time stored separately; configurable basis for the 50/90 km rule; unknown shown as unknown.
5. Source links are structurally validated only; verification state is stored and reviewed separately.
6. Tell the curator keeps originals, shows interpretation, lets participants edit/confirm/cancel; unsupported input becomes a note.
7. Refinement chips filter existing cards only; unknown data never counts as a match; empty state offers removing filters or a confirmed research request.
8. Login defaults: two provisioned accounts, no sign-up, 7-day sessions, 5 failures → 15-minute lock, admin password reset that revokes sessions.
9. Milestones A (board, demo, history, navigation, input UI), B (persistence, auth, reactions, plans, completion, input confirmation, learning/preferences), C (contracts, validation, idempotency, tests, setup diagnostics, docs, deployment config).

## UI refinements (2026-10-14, second review)
- "Tell the curator" is docked above the bottom navigation (not floating over content); page bottom padding reserves its space; the dock hides while the on-screen keyboard is open.
- Collapsed cards show name, why now, effort, date/window, a one-line practical summary ("Not yet known: …") and participant actions; research fields and explicit unknowns are behind "View details".
- Walking feedback: explicit "This was about an outing: <name>" options (asks which when several), a personal "use less walking" preference with editable wording and no invented number, and "Just keep this as a note".
- Cards below 70 state that they are below the publication threshold; the demo 59/100 card is labelled as deliberately below it and is rejected by the server.
