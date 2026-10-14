# Curation rules (implemented in `backend/curator/domain`)

## Score model (`scoring.py`)
| Component | Max |
|---|---|
| uniqueness | 25 |
| low_crowd | 20 |
| preference_fit | 15 |
| timing (seasonal/timing fit) | 15 |
| evidence (quality) | 15 |
| practicality (from Burlington) | 10 |
`fit_score` = sum (each component validated 0..max). **Separate** from `evidence_status`
(`none | unreviewed | partially_reviewed | reviewed`). A high fit score does not prove facts.

## Publication (`publication.check_candidate`, `validate_batch`)
A candidate is eligible only when **all** hold:
1. `dataset == "real"` (demo never publishable).
2. `fit_score >= 70`.
3. ≥ 1 evidence source with a URL, and ≥ 1 of those with `verification_status = reviewed_supports_claim`.
   URL format validation is structural; it does not prove the page supports the claim.
4. No active exclusion on destination, experience or category (expired temporary exclusions ignored).
5. Same canonical destination not in a published batch within 60 days unless `repeat_exception` is stored.
6. A prior visit to the same destination (other than a drive-through) requires `novelty_explanation` or
   `repeat_exception`. Undated historical visits count forever — history is never forgotten after 60 days.
7. Generic categories (park, waterfall, conservation_area, trail) require a `distinct_angle`.
8. Dated events need an upcoming, non-cancelled occurrence.
9. Distance on the configured basis: > exceptional → blocked; > primary needs `exceptional_distance`. Unknown → warning.
Published batch: 2–5 items, all eligible, no duplicate destination; < 2 categories → warning. Fewer qualified
items → publish `insufficient_candidates` with a note, never pad.

## Deduplication
Destinations carry `normalized_names` (name + aliases, lower-case, punctuation and "Ontario/ON/the" stripped).
Candidate ingestion matches by id, then normalised name/alias, and merges aliases. Offered options
(`batch_items`) are stored separately from visits.

## Historical memory
- Drive-throughs (Milton, Cambridge, Caledonia) never block experiences there.
- Town visits (Paris, Elora, Niagara Falls) require an explanation of how a new experience differs.
- Broad notes (many waterfalls/parks, three conservation areas) feed rule 7, not a blanket nature ban.

## Input routing (`interpreter.py`, `services/inputs.py`)
Pipeline: capture original → participant + context (selected plan, recent visits, focused card) → intents →
proposed changes → clarification if ambiguous → participant edits → confirm → apply → audit.
| Phrase type | Result |
|---|---|
| URL | `create_idea` (event lead), link marked unverified |
| "drove through X" | historical drive-through visit, explicit "does not block X" |
| "we went there / to X yesterday" | clarification: complete selected plan / record separate visit / note |
| "too much walking" | clarification: about a specific recorded outing (asks which when several) / less walking for my future suggestions (personal, editable wording, no invented number) / note |
| "liked it but not the crowd" | feedback on the last visit + tentative observation (never from demo visits) |
| "not another waterfall", "easy", "nothing expensive", "indoors" | constraint, default **today only, shared**, editable |
| "one main stop, food nearby" | ongoing shared preference (awaits the other participant) |
| "save this for next month" | save interest when opened from a card, else clarification |
| "4/5", "5 stars" | rating for the last visit, else clarification |
| question | answer from stored records only + optional research request |
| anything else | general note |
Temporary constraints expire at the end of the Toronto day. Shared ongoing preferences wait for the other
participant. Personal preferences can only be edited by their owner. One negative reaction never becomes a rule.

## Refinement chips (frontend `lib/refine.ts`)
Filter existing cards for the session. Unknown data is never a match (counted as "hidden because unknown").
No new options are generated. "Save this as a preference" goes through Tell the curator confirmation.
