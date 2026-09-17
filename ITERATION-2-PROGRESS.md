# CareerTimeMachine - Team Progress & Change Log

Living document. Everyone updates their own section as they make progress. This is our shared history: what has been done, what is in progress, what is left, and what is blocking who.

## How to use this file (read before editing)

- Find your section (Frontend, Backend, Database, Security, AI). Add your update there.
- Add a new numbered entry at the **top** of your section's log. Never overwrite or delete old entries - this file is our version history.
- Numbering is `AREA <iteration>.<n>`, e.g. `SEC 2.1`, `SEC 2.2`. Iteration 2 = the `2.x` series. The next iteration will be `3.x`.
- Every entry states: status, owner, date, what changed, why, and any blocker (what you are waiting on, or what your work now unblocks).
- If your work is blocked by, or blocks, another team, **also** add a row to the Cross-team blockers table so it is visible to everyone.
- Keep entries short. One or two lines each.

## Status legend

- `[DONE]` - finished and verified
- `[WIP]` - in progress
- `[BLOCKED]` - cannot proceed, see blocker
- `[TODO]` - planned, not started

## Entry template (copy this)

```markdown
### AREA 2.x - short title

- **Status:** [TODO] **Owner:** name **Date:** YYYY-MM-DD
- **What:** what changed or was built.
- **Why:** the reason / what it enables.
- **Blocks / Blocked by:** who is waiting on this, or what you are waiting on. "none" if standalone.
```

## Iteration 2 goals

1. **Workplace Scenarios** - an LLM (that we are training) turns each user's captured profile into personalised workplace scenario questions to practise.
2. **Save user progress** in the database so a returning user resumes where they left off instead of repeating scenarios.
3. **Move toward a sign-on method.** Token generation is in scope this iteration; a TOTP authenticator sign-on (suggested by our tutor) is a possibility for Iteration 3.
4. **Fix the confirmed Iteration 1 pen-test finding** (CTM-F-001) and the security hardening items.

## Cross-team blockers (live - keep this current)

| #   | Blocker                                                                                                                                                                                                   | Raised by | Needs (owner)                                                            | Status           |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------ | ---------------- |
| B1  | LLM output format is not yet agreed. Backend has now built the scenario endpoints against a proposed provider contract (`backend/app/providers/scenario_provider.py`) using a curated development provider, but production AI scenarios and feedback cannot be connected until the contract is agreed. Frontend/product also sent the AI team a data-contract proposal for role prediction (role + skills in, predicted role(s) out) and MCQ matching (role + skills + difficulty in, matched against their pre-trained question set out), plus a note that the backend integrates with one point of contact only, never their external LLM directly - still awaiting the AI team's confirmation (2026-09-17) | Backend, Frontend | AI to agree (or amend) the proposed contracts and implement the production `ScenarioProvider` and role-prediction endpoint | `[BLOCKED]` open |
| B2  | ~~Sessions and profiles~~ now persist to Postgres (DB 2.5/FE 2.7, 2026-09-15) - restart-proof, verified live. Still in-memory: the selected practice role and practice sessions/responses/feedback, so that part of user progress is still lost on restart. FE 2.11's practice-progress persistence (which activities are done) is currently `sessionStorage` only - survives a reload but not closing the browser - so it needs this same database work. AC 4.3.4 was updated (2026-09-17, see `AC_Full_Review_Epic4.docx`) to explicitly require database-backed restoration after leaving and returning, not just an active session, so this is now a named acceptance criterion, not just an implied gap | Backend   | Database to add 2 practice-role columns on `profile` and practice session/response/feedback tables - see backend handover section 8 | `[WIP]` open |
| B3  | Sign-on method for Iteration 2 not finalised (token generation now, TOTP later) - affects the frontend sign-on screen and the security design                                                             | Security  | Team decision, then Security to spec the token flow                      | `[WIP]` open     |

---

## Frontend (FE)

**Iteration 1 baseline** `[DONE]`: cards 1-7 UI (Get Started, Previous IT Experience, Skills & Experience, Career Break, Review Profile, Skills & Industry Relevance, Skill/Industry detail). Talks to the API using the `X-Session-Token` header, hash-based routing.

### FE 2.11 - AC 4.4.1-4.4.2/4.5.1-4.5.3 - Multi-activity workplace practice, reflective feedback, session completion

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-17
- **What:** replaced the earlier single-shared-activity assumption - each
  role-relevant workplace area now has its own real MCQ activity, not one
  shared activity for the whole session - after new reference designs
  clarified the intended flow (this reverses two calls made in an earlier
  version of this section: dropping duration, and giving only one area a
  real activity). Built the MCQ activity screen (AC 4.4.1/4.4.2) -
  single-selection options, nothing pre-selected, Continue disabled until
  she picks one, a "Worth remembering" hint. Built the reflective feedback
  screen (AC 4.5.1/4.5.2) - what worked well, what to consider, and a skill
  to explore, with no score/pass-fail/correct-incorrect wording anywhere.
  Built "Next activity" progression through all of a role's relevant areas
  (AC 4.5.3), a "Practice complete" session summary (role, focus, duration/
  difficulty, activities completed, last skill to explore), and the inline
  "Practice summary coming soon" placeholder. Which activities are done now
  persists across a reload alongside the rest of the practice state. Also
  fixed a real bug: the area detail popup opened full-canvas-height and
  could cover the very hotspot just clicked - it's now a compact card that
  opens on whichever side keeps that hotspot visible. Authored full
  3-activity mock content for Business Analyst, Data Analyst and Software
  Developer, one hand-written activity for each of the other 11 roles, and
  a generic fallback so every relevant area always opens something real.
- **Why:** closes out US 4.4 and US 4.5 end to end on the frontend (Epic
  4.0's full acceptance criteria, MCQ-only scope for this iteration), using
  mock data shaped to match the real AI contract once agreed. Also sent the
  AI team a data-contract proposal (role + skills in for role prediction;
  role + skills + difficulty in for MCQ matching against their pre-trained
  question set; the backend never calls their external LLM directly, only
  their one integration point) and a consolidated AC review of all of Epic
  4.0, which explicitly supersedes two earlier, narrower documents once the
  new reference designs corrected the duration and single-activity
  assumptions above.
- **Blocks / Blocked by:** blocked by B1/AI 2.1 for real predicted roles and
  real (pre-trained, not mock) MCQ content - proposal sent to the AI team,
  awaiting confirmation. Coding activities (AC 4.4.2's other interaction
  types, AC 4.4.3) are explicitly out of scope for this iteration per
  product decision - moved to a later iteration's backlog.

### FE 2.10 - AC 4.3.1-4.3.4 - Interactive Workplace

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-16
- **What:** built the interactive workplace screen - a clickable hotspot
  map over `assets/workplace.png`, filtered by role relevance
  (`mockData/workplaceAreas.js`'s `ROLE_AREAS` mapping) so only areas
  relevant to the user's selected role are coloured and clickable; every
  other area is genuinely disabled, not just styled - a real requirement,
  not just the Figma sample's "everything selectable." The scenario banner
  shows the current situation with a hide/show toggle. Practice role,
  duration, difficulty and progress persist across a reload via
  `sessionStorage` (`practiceSession.js`).
- **Why:** closes out US 4.3 end to end on the frontend.
- **Blocks / Blocked by:** none - fully working against mock data.

### FE 2.9 - AC 4.2.1/4.2.2/4.2.3 - Practice intro, setup and preparation

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-16
- **What:** fixed AC 4.2.1's exception message to the exact required text
  ("We couldn't load your practice introduction. Please try again.").
  Built AC 4.2.2 (Select Practice Time and Difficulty) - duration
  (Quick/Standard/Extended) and difficulty (Easy/Standard/Complex,
  matching the AC's wording) as two independent selections, nothing
  pre-selected, "Choose a practice time and difficulty to continue" until
  both are chosen. Built AC 4.2.3 (Review Practice Preparation) - shows
  the selected role, practice focus, the skills she'll use, a new
  in-demand skill not already on her profile (real data via
  `GET /career-translation`'s `new_horizons`), and the chosen duration/
  difficulty, with an Enter Workplace button that carries all of it into
  the workplace session.
- **Why:** closes out US 4.2 end to end on the frontend, using mock
  scenario data shaped to match the eventual real contract.
- **Blocks / Blocked by:** mock scenario data
  (`mockData/practiceScenario.js`) stands in for BE 2.1/AI 2.1-2.2;
  swapping to the real endpoint is a small change once those land.

### FE 2.8 - Real-token bug fixes from live testing

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-15
- **What:** fixed three real bugs found while testing the real token end
  to end: (1) the token display modal overflowed the page on a real
  43-character token - `.atm-token-value` now wraps (`word-break:
  break-all`) instead of forcing a horizontal scrollbar; (2) clicking
  "Continue your journey" on an unconfirmed profile hit Career Journey's
  409 and showed a raw error instead of resuming the wizard; (3) leaving
  the wizard mid-way and returning via "Career Journey" always restarted
  at Your Story instead of resuming where she left off. Fixed both
  redirect bugs with a shared `getResumeStep(profile)` helper (checks
  whether the role/break steps are actually complete) used consistently in
  `CareerJourney.jsx`, `LandingPage.jsx` and `useAccessTokenFlow.js`.
- **Why:** all three were found through the user's own live testing of
  FE 2.7's real-token integration, not caught by the existing test suite.
- **Blocks / Blocked by:** none.

### FE 2.7 - Real backend token (replaces the client-side mock)

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-15
- **What:** followed `BACKEND_HANDOVER_ITERATION_2.md` section 3 - Generate
  Token now calls the real `POST /anonymous-sessions` and shows the actual
  43-character token (no more `CTM-XXXX-XXXX` client-side format). Entering
  an existing token validates it against `GET /anonymous-sessions/current`
  (`api.validateToken`) before switching sessions, with distinct messages
  for "not recognised" (401) vs "couldn't verify" (network/5xx) - one
  request, no duplicate check. Removed `api.js`'s silent 401-retry (a dead
  token now surfaces as a real error instead of silently starting an empty
  session). An unconfirmed profile now resumes at Your Story instead of
  hitting Career Journey's 409; a confirmed one still gets "Welcome back".
  Deleted the whole `accessToken.js` mock/mapping layer
  (`isKnownToken`/`recordTokenSession`/`getSessionForToken`/etc.) - it's
  now a thin wrapper over `api.js`'s one real token.
- **Why:** BE 2.3/BE 2.9 delivered the real endpoints; this closes the loop
  so every already-built wizard screen (Your Story - Your Direction) saves
  against a real, persistent token instead of a client-side mock mapping.
- **Blocks / Blocked by:** none - fully working now that DB 2.5/BE 2.9
  landed. Practice-role and workplace-scenario screens are a separate,
  not-yet-started piece (deferred per Thiri, 2026-09-15).

### FE 2.6 - Returning-user journey retrieval hardening

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-14
- **What:** closed a gap found while verifying the returning-user flow -
  since sessions are in-memory only, a server restart or Cloud Run cold
  start can wipe the backend session behind an access token, and the
  existing 401-retry logic would silently swap in a brand new empty
  session instead of failing loudly. Entering an existing token now
  checks the restored profile is actually confirmed before continuing;
  if not, it shows "We couldn't load your saved journey. Please try
  again." with Try Again instead of opening an empty Career Journey.
  Also added the same load-error handling to Your Direction ("We
  couldn't load the information needed for this activity."), so saved
  data reliably reaches it once a session is restored.
- **Why:** covers AC 3.3.1 (retrieve saved career information - "do not
  display incomplete or incorrect saved information") and the Your
  Direction half of AC 3.3.2 (saved info available to journey features).
- **Blocks / Blocked by:** the rest of AC 3.3.2 (feeding role/skills/
  responsibilities to Workplace Practice for scenario generation, and
  making data available to the future ePortfolio) is blocked - neither
  feature exists yet (Workplace Scenario is still a placeholder, blocked
  on B1/BE 2.1; ePortfolio has no page). The "redirect to the specific
  page where missing info was entered" exception is also not built yet -
  needs a decision on scope before picking it up.

### FE 2.1 - Workplace Scenarios screen

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** new screen that requests a personalised scenario, shows the question(s), lets the user answer, and shows the result.
- **Why:** the core Iteration 2 user-facing feature.
- **Blocks / Blocked by:** blocked by B1 (needs the agreed LLM scenario contract) and BE 2.1.

### FE 2.2 - Progress / resume UI

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** show which scenarios are done vs remaining; resume from where the user left off.
- **Why:** goal 2 - returning users continue rather than repeat.
- **Blocks / Blocked by:** blocked by BE 2.2 (progress endpoints) and B2.

### FE 2.3 - Sign-on screen (placeholder)

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-13
- **What:** Access Your Journey modal (generate new / enter existing token), the
  generated-token display with copy, existing-token validation with the
  empty/invalid error states, token-dependent nav gating (Career Journey,
  Practice Scenarios, ePortfolio) with the "access token required" notice,
  and the My Token view once a token is active. All exception-condition
  messages from AC 3.1.1-3.1.5 are wired up. Token-based, designed so TOTP
  can slot in later.
- **Why:** goal 3 - covers the full frontend side of sign-on for this
  iteration end to end.
- **Blocks / Blocked by:** the token itself is a client-side mock
  (sessionStorage only, see `frontend/src/accessToken.js`) - frontend is no
  longer blocked by B3, but real persistence still needs B2/DB 2.1 and a
  real backend-issued token still needs BE 2.3. Once those land, only
  `accessToken.js` needs to change, not this UI.

  ### FE 2.5 - Career Journey: save, edit and update confirmed career info

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-14
- **What:** redesigned Career Journey into a 4-step timeline (Your Story,
  Your Experience, Your Break, Skill Relevance Map) with Edit/View actions,
  showing "Welcome back" on first entry via an existing token vs "Your
  Career Journey" otherwise. Added a shared fixed TopNav across every
  screen (landing, all wizard steps, Career Journey), so navigation and the
  token pill are consistent everywhere. Finishing the wizard now routes to
  a new Workplace Scenario placeholder instead of Career Journey. Edit
  buttons route back into the relevant wizard step pre-filled with the
  saved data; that step's existing Continue button now saves and returns
  directly to Career Journey (instead of continuing the linear wizard),
  with "couldn't load"/"couldn't save" exception messages and a Try Again
  button on both the wizard steps and Career Journey itself. Also fixed a
  real bug found while testing: saving an edit cleared the backend's
  confirmed flag and crashed Career Journey on return - it now
  re-confirms the profile before navigating back.
- **Why:** covers AC 3.2.1 (save confirmed career info against the access
  token), 3.2.2 (retrieve saved info for editing) and 3.2.3 (update saved
  career info), end to end on the frontend.
- **Blocks / Blocked by:** same as FE 2.3 - the access token is still
  linked to its backend session via a client-side mock mapping (see
  `frontend/src/accessToken.js`), not a real `anon_session` row. Once
  BE 2.3/DB 2.1 land, that mapping layer goes away and the access token
  becomes the same identifier as the session token.

### FE 2.4 - Robustness + security hardening (frontend)

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** add an error boundary so a failed API call does not white-screen the app (seen during the pen test); add SRI `integrity` on the Google Fonts link (pen-test H-5); help add security headers at build/host level (H-3).
- **Why:** reliability + close pen-test hardening items.
- **Blocks / Blocked by:** coordinate with SEC 2.2.

---

## Backend (BE)

**Iteration 1 baseline** `[DONE]`: layered FastAPI (routes / schemas / services / repositories / interfaces). Anonymous sessions, catalogue endpoints, profile capture + confirm + delete, career journey, career translation, career direction, unified error envelope. All behind repository interfaces so storage can be swapped.

### BE 2.9 - Postgres-backed session and profile repositories

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-15
- **What:** new `PostgresSessionRepository`/`PostgresProfileRepository`
  (`app/repositories/postgres/`), wired into `dependencies.py` behind the
  same `HAS_DATABASE` check already used for the catalogue - no changes to
  routes, schemas or services, purely a repository swap behind the
  existing interfaces. Verified live: generated a token, saved a full
  profile (role, skills, responsibilities, break dates), killed and
  restarted the backend process twice, confirmed everything was still
  there both via direct API calls and through the real frontend UI.
  Skipped `practice_role_id`/`practice_role_source` (no columns for them
  yet - separate schema change, see B2) and practice sessions (still
  in-memory, unrelated tables). Also fixed a test-isolation gap this
  surfaced: `tests/conftest.py` only faked the catalogue repository, not
  session/profile, so tests using fixture-only role ids (e.g.
  `"software_engineer"`, not a real `role` row) started hitting genuine
  foreign-key violations once those repos could be real. Added a matching
  autouse fixture that swaps session/profile for fresh in-memory stores
  per test. All 300 tests pass again (offline, ~4s, unchanged from before).
- **Why:** closes the "restart loses everything" gap for tokens and
  profiles (BE 2.3/BE 2.7's stated caveat) - the actual blocker was DB 2.1
  wiring, not a technical limitation, once DB 2.5 seeded the tables the
  real repositories needed.
- **Blocks / Blocked by:** paired with DB 2.5 (seeding). Practice role and
  practice session restart-persistence are still blocked on new
  tables/columns - see B2.

### BE 2.8 - Multiple-choice workplace activities

- **Status:** [BLOCKED] **Owner:** Mirza **Date:** 2026-09-14
- **What:** done locally - scenarios carry `activity_type`. **MCQs are active in Iteration 2:** each session serves a single-selection MCQ with stable option ids; unknown, other-scenario or wrong-field answers are rejected; feedback covers why the option may help, trade-offs, other considerations and a skill to explore (no score, pass/fail, correct/incorrect, readiness or employability). **Written responses are retained** for future iterations but not served. Curated provider only. 300 tests.
- **Why:** AC 4.4.2, 4.5.1-4.5.3; backend Subtasks 7-8.
- **Blocks / Blocked by:** restart persistence blocked by B2 (practice tables also need `activity_type`, options, `selected_option_id`, `trade_offs` - handover section 8). Production MCQs blocked by B1 (AI provider must follow the updated contract). FE 2.1 can build the MCQ screen against `API-CONTRACT.md` now.

### BE 2.7 - Selected practice role

- **Status:** [BLOCKED] **Owner:** Mirza **Date:** 2026-09-14
- **What:** done locally - `GET`/`PUT /practice-role` saves the previous or predicted role, rejects invalid role ids, and hands the saved role and career context to workplace practice so nothing is re-entered. 25 tests.
- **Why:** backend Subtask 5 / AC 4.1.2.
- **Blocks / Blocked by:** surviving a restart is blocked by B2 (`practice_role_id`, `practice_role_source` columns). Your Direction needs to call it (FE). Predicted roles still need AI role predictions.

### BE 2.6 - Offline test suite and backend handover

- **Status:** [DONE] **Owner:** Mirza **Date:** 2026-09-14
- **What:** `backend/tests/conftest.py` gives tests a fixed catalogue, fixing 10 tests that failed without a database `.env`. Full suite 192 passed. Added `backend/docs/BACKEND_HANDOVER_ITERATION_2.md` (card status, frontend integration steps, DB/AI needs) and updated `API-CONTRACT.md`.
- **Why:** reliable tests; lets frontend, database and AI integrate against the documented API.
- **Blocks / Blocked by:** contract review with FE, DB and AI still needed.

### BE 2.1 - Workplace Scenario endpoints

- **Status:** [BLOCKED] **Owner:** Mirza **Date:** 2026-09-14
- **What:** done locally - start/resume/complete practice sessions (`/practice-sessions`) and submit a response with reflective feedback (no score, pass/fail or judgement). Scenario generation sits behind `ScenarioProvider` with validated output, a timeout and a controlled 503. A **curated development provider** supplies scenarios for now - this is not the AI integration.
- **Why:** serves the Workplace Scenarios feature (backend Subtasks 6-8).
- **Blocks / Blocked by:** production scenarios blocked by B1 (AI provider). FE 2.1 can build against the documented contract now.

### BE 2.2 - Progress persistence endpoints

- **Status:** [BLOCKED] **Owner:** Mirza **Date:** 2026-09-14
- **What:** done locally - responses saved with timestamps, duplicate submissions rejected, progress on every session response and at `GET /practice-sessions/{id}/progress`, resume via `GET /practice-sessions/current`. Stored in-memory behind `PracticeSessionRepository`.
- **Why:** goal 2 - resume, no repeats.
- **Blocks / Blocked by:** surviving a restart is blocked by B2 (practice tables). FE 2.2 can build against the documented contract now.

### BE 2.3 - Token generation for sign-on

- **Status:** [DONE] **Owner:** Mirza **Date:** 2026-09-14
- **What:** `POST /anonymous-sessions` issues a random 43-character token and stores only its SHA-256 hash; `GET /anonymous-sessions/current` validates a token without echoing it; unknown and malformed tokens get the same 401; cross-token isolation and "no token in logs" tested. Still swappable for TOTP later.
- **Why:** goal 3; US 3.1-3.3.
- **Blocks / Blocked by:** frontend can replace the `accessToken.js` mock now (handover section 3). Restart persistence blocked by B2. Token expiry policy still needs a decision (B3).

### BE 2.4 - Fix CTM-F-001 (broken atomicity on PATCH /profile)

- **Status:** [DONE] **Owner:** Mirza **Date:** 2026-09-14
- **What:** `ProfileService.update_profile()` now validates a copy and saves only a fully valid update, and the memory repository copies profiles in and out, so a rejected update leaves the stored profile unchanged. Regression tests in `backend/tests/test_profile_update_state.py` (CTM-PT-005b pattern). `PATCH /career-direction` already validated before changing anything.
- **Why:** fixes the one confirmed pen-test vulnerability (integrity issue: a rejected update still partly saved).
- **Blocks / Blocked by:** ready for the SEC 2.1 retest.

### BE 2.5 - Input caps (hardening)

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** add `max_length` on free-text fields (H-1) and a max list size (H-2) in the Pydantic schemas.
- **Why:** storage hygiene and abuse resistance before the DB goes live.
- **Blocks / Blocked by:** none.

---

## Database (DB)

**Iteration 1 baseline** `[DONE]`: `role`, `skill`, `role_skill` tables live in Postgres and drive roles/skills. Other catalogue lists still come from in-memory placeholders. Sessions and profiles are **not** persisted (in-memory only).

### DB 2.5 - Seeded 3 catalogue tables; sessions/profiles now persist

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-09-15
- **What:** seeded `experience_option`, `responsibility` and `return_status`
  directly in the live database with the exact ids/labels already used by
  the mock catalogue fallback (`data/schema/seed_placeholder_catalogues.sql`)
  - no new schema, just rows, since `profile` has foreign keys into these
  and they were empty, which blocked any real profile save past role/skills.
  This substantially completes DB 2.1 (sessions/profiles now genuinely
  persist - see BE 2.9) and partially completes DB 2.3.
- **Why:** DB 2.1 was blocked on exactly this - the Postgres repositories
  existed in design but every write would have failed on a foreign-key
  violation without these rows.
- **Blocks / Blocked by:** **not seeded** - `career_area` (pending real
  content from the AI role-prediction work; has `growth_outlook`/
  `evidence_source`/`source_date` columns meant for sourced data, not a
  placeholder list) and `break_reason` (field is being removed from the
  wizard UI, so nothing needs it). DB 2.3 remains open for those two plus
  real (non-placeholder) content generally. Practice-role columns and
  practice session tables (B2) are unrelated, still open.

### DB 2.1 - Persist sessions and profiles

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** create tables for anonymous sessions and profiles matching the backend's data model; provide connection details for the backend `.env`.
- **Why:** without this, all user state is lost on restart - blocks progress saving.
- **Blocks / Blocked by:** blocks B2, BE 2.2.

### DB 2.2 - Progress storage

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** table(s) for scenario progress (which scenarios a user has done, their answers/results, timestamps).
- **Why:** goal 2 - resume / no repeats.
- **Blocks / Blocked by:** blocks BE 2.2. Coordinate the shape with AI (scenario ids).

### DB 2.3 - Seed remaining catalogue tables

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** fill the responsibilities, break-reasons, return-statuses and career-areas tables (currently placeholder-only) with real data; keep ids stable.
- **Why:** removes the in-memory placeholder fallback.
- **Blocks / Blocked by:** none.

### DB 2.4 - Startup mode indicator (pen-test R09)

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** make the app log at startup whether it is using the database or the in-memory fallback.
- **Why:** the pen test flagged silent fallback to mock data as a risk.
- **Blocks / Blocked by:** small, do with backend.

---

## Security (SEC)

**Iteration 1 baseline** `[DONE]`: full pen test (local) + passive verification (live). Result: 1 confirmed vulnerability (CTM-F-001, Medium), 5 hardening recommendations (H-1 to H-5), 1 item for a team policy decision (`/docs` exposure). Cross-session isolation, CORS, stored-XSS resistance and error handling all passed.

### SEC 2.1 - Remediate CTM-F-001 and retest

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** verify the BE 2.4 fix, then re-run pen-test CTM-PT-005b locally and repeat the check on the live deployment.
- **Why:** closes the only confirmed vulnerability.
- **Blocks / Blocked by:** pair with BE 2.4.

### SEC 2.2 - Security headers (H-3)

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** add `Content-Security-Policy`, `X-Frame-Options` (or CSP `frame-ancestors`) and `X-Content-Type-Options` on frontend and backend responses. Confirmed still missing on the live site.
- **Why:** overdue hardening, now confirmed live.
- **Blocks / Blocked by:** coordinate with FE 2.4.

### SEC 2.3 - Rate limiting (H-4)

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** add rate limiting, including on anonymous session creation (currently unbounded).
- **Why:** pen-test H-4 / team risk R05.
- **Blocks / Blocked by:** with backend.

### SEC 2.4 - /docs and /openapi.json exposure decision

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** team decides whether the API schema stays public on the live backend; record the decision here.
- **Why:** flagged in the pen test as a policy call, not an automatic finding.
- **Blocks / Blocked by:** needs a team decision.

### SEC 2.5 - Sign-on design (token now, TOTP later)

- **Status:** [WIP] **Owner:** TBD **Date:** TBD
- **What:** spec the token-generation sign-on for this iteration. Also research a TOTP authenticator method for Iteration 3 as suggested by the tutor. Note: TOTP (RFC 6238, time-based one-time passwords, e.g. Google Authenticator) is not yet understood by the team - the action is to research a Python approach (for example the `pyotp` library and a QR provisioning URI) and write it up before committing to it. TOTP is a possibility for this iteration only if time allows; the plan is token this iteration, TOTP in Iteration 3.
- **Why:** goal 3.
- **Blocks / Blocked by:** B3. Blocks FE 2.3, BE 2.3.

### SEC 2.6 - Threat-model the new surfaces

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** extend the threat model to cover the LLM (prompt injection, PII leakage, unsafe output) and the new auth flow (risk R11 was reserved for this).
- **Why:** new features add new attack surface.
- **Blocks / Blocked by:** after the AI and auth designs exist.

---

## AI (AI)

New for Iteration 2. Goal: an LLM we are training that turns a user's captured profile (role, years, skills, break, direction) into personalised workplace scenario questions.

### AI 2.1 - Define the scenario contract

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** agree the exact request (which profile fields the model receives) and response (the JSON shape of a scenario: id, prompt/question, options or expected-answer form, scoring) that the backend will consume.
- **Why:** everything downstream (backend endpoints, frontend screen, progress storage) depends on this shape.
- **Blocks / Blocked by:** blocks B1, BE 2.1, FE 2.1, DB 2.2.

### AI 2.2 - Model and training

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** decide the model/provider, gather/prepare training data, design prompts, and produce structured, validated output.
- **Why:** the engine behind Workplace Scenarios.
- **Blocks / Blocked by:** none to start; feeds AI 2.1.

### AI 2.3 - Serving and guardrails

- **Status:** [TODO] **Owner:** TBD **Date:** TBD
- **What:** expose the model to the backend behind an agreed interface; add guardrails (no leaking of personal data, safe/appropriate content, predictable output the backend can parse).
- **Why:** safe, reliable integration.
- **Blocks / Blocked by:** coordinate with SEC 2.6 and BE 2.1.
