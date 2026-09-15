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
| B1  | LLM output format is not yet agreed. Backend has now built the scenario endpoints against a proposed provider contract (`backend/app/providers/scenario_provider.py`) using a curated development provider, but production AI scenarios and feedback cannot be connected until the contract is agreed | Backend   | AI to agree (or amend) the proposed contract and implement the production `ScenarioProvider`            | `[BLOCKED]` open |
| B2  | Sessions, profiles, the selected practice role and practice sessions/responses/feedback are still in-memory (lost on restart), so user progress cannot be persisted yet                                                                                                     | Backend   | Database to provide session/profile tables, 2 practice-role columns on `profile`, practice session/response/feedback tables, seeded catalogue tables (profile FKs) + connection details - see backend handover section 8 | `[BLOCKED]` open |
| B3  | Sign-on method for Iteration 2 not finalised (token generation now, TOTP later) - affects the frontend sign-on screen and the security design                                                             | Security  | Team decision, then Security to spec the token flow                      | `[WIP]` open     |

---

## Frontend (FE)

**Iteration 1 baseline** `[DONE]`: cards 1-7 UI (Get Started, Previous IT Experience, Skills & Experience, Career Break, Review Profile, Skills & Industry Relevance, Skill/Industry detail). Talks to the API using the `X-Session-Token` header, hash-based routing.

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
