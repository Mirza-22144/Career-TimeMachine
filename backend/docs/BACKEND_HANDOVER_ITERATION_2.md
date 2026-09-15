# Backend Handover - Iteration 2

| | |
|---|---|
| Date | 2026-09-14 |
| Branch | `iteration-2-backend` |
| Backend scope | Token and career-profile continuity (US 3.1-3.3), CTM-F-001, selected practice role (AC 4.1.2), workplace-practice sessions, scenario provider boundary, multiple-choice (active) and written-response (retained) activities, responses, reflective feedback and progress |
| Contract reference | `backend/docs/API-CONTRACT.md` (also live at `/docs` when the API runs) |

**Read this first:** everything below works end to end locally, but it is
**not** a production integration yet:

- Storage is **in-memory**. Tokens, profiles, practice roles and practice
  sessions are lost when the API restarts.
- Scenarios and feedback come from a **curated development provider**, not the
  AI/LLM component.
- **Multiple-choice questions (MCQs) are the active workplace activity in
  Iteration 2.** Every practice session serves a single-selection MCQ. Written
  responses remain supported in the backend for future iterations but are not
  served in Iteration 2.

## 1. Backend card status

| Card | Status | Evidence / what is left |
|---|---|---|
| Subtask 1 - Confirm API contract | **Partial** | Endpoints, request/response examples, error codes and ownership documented in `API-CONTRACT.md` and this handover. **Left:** review with frontend, database and AI owners. |
| Subtask 2 - Fix CTM-F-001 | **Done** | Validation runs on a copy; only a fully valid update is saved. `tests/test_profile_update_state.py`. **Left:** Security retest (SEC 2.1). |
| Subtask 3 - Persistent token and profile repositories | **Blocked** | Interfaces kept as the boundary; only token hashes are stored; memory repos copy data like a DB. **Blocked on database:** see section 8. DB-backed repositories and DB-error mapping not written. |
| Subtask 4 - Returning-user token access | **Done** (restart caveat) | Valid token restores profile, journey, practice role and practice session; missing/malformed/unknown tokens get a consistent 401; no raw token in storage, logs, URLs or later responses; cross-token tests. `tests/test_token_access_api.py`. |
| Subtask 5 - Save selected practice role | **Partial** | Save/retrieve, previous vs predicted, invalid ids rejected, used by session start, no re-entry. **Blocked:** survives application restart (database). `tests/test_practice_role_api.py`. |
| Subtask 6 - Practice session setup | **Partial** | Start with valid token and saved role; duration/difficulty validated; owner, role, settings, status, timestamps recorded; retrieval after refresh; isolation; clear 409s for missing profile/role. **Blocked:** retrieval after restart (database). `tests/test_practice_sessions_api.py`. |
| Subtask 7 - Scenario provider | **Done (backend boundary)** / **Blocked (AI provider)** | `ScenarioProvider` interface and validated contract with an explicit `activity_type` (`multiple_choice` active, `written_response` retained); MCQs need 2-6 options with unique ids and no correctness field; minimal input; output validation, including that the requested activity type is returned; curated provider serves MCQs for dev/tests; timeout, failure and invalid output return a controlled 503; provider code not in routes/repositories; nothing executed. **Blocked on AI owner:** production provider. `tests/test_scenario_provider.py`, `tests/test_practice_activity_contract.py`. |
| Subtask 8 - Responses, feedback and progress | **Partial** | MCQ answer (`selected_option_id`) or written answer (`response_text`) accepted only for a scenario in the user's active session; the option must belong to that scenario; the wrong answer field for the activity type is rejected; linked to token, session and scenario; duplicates return 409 and keep the first answer; MCQ feedback explains why the option may help, trade-offs, other considerations and a skill to explore; no score, pass/fail, correct/incorrect, readiness or employability fields or wording; progress retrievable; resume with same token. **Blocked:** resume after restart (database). `tests/test_multiple_choice_responses_api.py`, `tests/test_scenario_responses_api.py`, `tests/test_memory_practice_session_repository.py`. |
| Subtask 9 - Validation and access controls | **Done** (new endpoints) | Types, allowed values and length limits on all new fields; unexpected fields rejected (422); ownership checked before every read/change; errors carry no stack traces or provider details; tokens, profile content and responses not logged; CORS still env-based. Existing profile free-text caps are a separate item (BE 2.5). |
| Subtask 10 - Test, document, hand over | **Partial** | 300 tests pass; OpenAPI matches routes; contract and handover updated. **Left:** repository tests against a real database; LeanKit card updates. |

## 2. Endpoints

All paths are under `/api/v1`. Protected endpoints need:

```http
X-Session-Token: <access token>
Content-Type: application/json
```

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/anonymous-sessions` | Generate a new access token (no header) |
| `GET` | `/anonymous-sessions/current` | Validate an existing token |
| `GET` / `PATCH` / `DELETE` | `/profile` | Load / save or edit / delete career information |
| `POST` | `/profile/confirm` | Confirm saved information |
| `GET` | `/career-journey` | Returning-user Career Journey data (409 until confirmed) |
| `GET` / `PATCH` | `/career-direction` | Your Direction selections |
| `GET` | `/career-translation` | Skill Relevance Map |
| `GET` / `PUT` | `/practice-role` | Selected previous or predicted practice role |
| `POST` | `/practice-sessions` | Start workplace practice |
| `GET` | `/practice-sessions/current` | Resume the active session |
| `GET` | `/practice-sessions/{session_id}` | Read one session |
| `POST` | `/practice-sessions/{session_id}/complete` | Complete the session |
| `POST` | `/practice-sessions/{session_id}/scenarios/{scenario_id}/response` | Submit a response, get reflective feedback |
| `GET` | `/practice-sessions/{session_id}/progress` | Practice progress |

Full request/response examples and every error code are in `API-CONTRACT.md`.
The most important shapes:

**Generate token** - `POST /anonymous-sessions` → `201`

```json
{ "token": "<43 URL-safe characters>", "created_at": "2026-09-14T09:00:00Z", "last_seen_at": "2026-09-14T09:00:00Z" }
```

This is the only response that contains the token. The backend stores only its
SHA-256 hash and cannot show it again.

**Validate token** - `GET /anonymous-sessions/current` → `200`
`{ "created_at": ..., "last_seen_at": ... }` or `401`
`{"error": {"code": "HTTP_401", "message": "Invalid session token", "details": []}}`.

**Save practice role** - `PUT /practice-role`
`{ "role_id": "software_engineer", "source": "previous" }` → `200`
`{ "role_id": "software_engineer", "role_label": "Software Engineer", "source": "previous" }`.

**Start practice** - `POST /practice-sessions`
`{ "duration": "standard", "difficulty": "guided" }` → `201` session object with
`role`, `duration_minutes`, `scenarios[0]` (`title`, `workplace_area`,
`situation`, `task`, `activity_type: "multiple_choice"`, `options`, `guidance`,
`skills_used`, `new_skill_focus`) and `progress`.

**Submit an MCQ answer** - `POST .../scenarios/{scenario_id}/response`
`{ "selected_option_id": "software_slow_release_b" }` → `201` with
`scenario.response.selected_option_id`, `scenario.feedback`
(`what_worked_well`, `trade_offs`, `areas_to_consider`, `skill_to_explore`),
`feedback_status` and updated `progress`. A written activity (not served in
Iteration 2) sends `{ "response_text": "..." }` instead.

## 3. Frontend integration - access token

The frontend currently generates a `CTM-XXXX-XXXX` token in the browser and maps
it to the backend session token in `localStorage` (`frontend/src/accessToken.js`,
`hooks/useAccessTokenFlow.js`). With the real backend **the access token and the
session token are the same value**, so the mapping layer is no longer needed.
Suggested changes (frontend owner; backend has not edited frontend code):

1. **Generate Token** (`handleGenerateToken`): call `api.createSession(true)` and
   show the returned `token`. Drop `generateMockToken()` and `recordTokenSession()`.
2. **Enter existing token** (`AccessTokenModal`): replace `isKnownToken(trimmed)`
   with `GET /anonymous-sessions/current` using the entered token.
   `200` → valid; `401` → "That token isn't recognised. Please check it and try
   again."; network error / `5xx` → "We couldn't verify your access. Please try again."
3. **Returning journey** (`handleValidToken`): `api.restoreSession(token)`, then
   `GET /profile`. `confirmed: true` → Career Journey; `confirmed: false` → Your Story.
4. **Stop the silent 401 retry in `api.js`.** `request()` creates a brand-new
   session on any `401`, which silently swaps a returning user into an empty
   journey (the issue FE 2.6 worked around). Surface the `401` instead.
5. **Storage:** keep one token key (today `ctm_session_token` in `api.js` and
   `ctm_active_token` in `accessToken.js`). `KNOWN_TOKENS_KEY` and
   `TOKEN_SESSION_MAP_KEY` can be removed.
6. **Copy text:** "Your token looks like CTM-XXXX-XXXX" no longer matches; real
   tokens are 43 characters of `A-Z a-z 0-9 - _`.

## 4. Frontend integration - workplace practice

| Frontend step | Backend call | AC copy for errors |
|---|---|---|
| Your Direction → "Try a Workplace Scenario" | `PUT /practice-role` with the chosen role and `source` | `400` → "We couldn't load your selected role. Please try again." |
| Practice setup → Continue | `POST /practice-sessions` `{duration, difficulty}` | `422` → "Choose a practice time and difficulty to continue."; `409 PRACTICE_ROLE_REQUIRED` → "Please select a role to continue."; `409 PROFILE_NOT_CONFIRMED` → send to the page where information is missing; `503 SCENARIO_UNAVAILABLE` → "We couldn't start your workplace practice. Please try again." |
| Preparation / workplace screen | Use the session object: `role`, `duration_minutes`, `difficulty`, `scenarios[0]` (`title`, `workplace_area`, `situation`, `task`, `activity_type`, `options`, `guidance`, `skills_used`, `new_skill_focus`) | - |
| Returning to practice / refresh | `GET /practice-sessions/current` | `404` → no active session; offer to start one |
| Submit an activity | `POST /practice-sessions/{id}/scenarios/{scenario_id}/response` with `{ "selected_option_id": "<option_id>" }` | `400 INVALID_OPTION_ID`, `400 ACTIVITY_TYPE_MISMATCH` or `422` → "We couldn't submit your response. Please try again."; `409 RESPONSE_ALREADY_SUBMITTED` → reload the session and show the saved answer; `feedback_status: "unavailable"` → "We couldn't generate your personalised feedback. You can continue to the next activity." |
| After feedback | `progress.current_scenario_id === null` while `status` is `active` | "You've completed the available activities for this practice session." |
| Finish | `POST /practice-sessions/{id}/complete` | - |

**Multiple-choice activity (active in Iteration 2):**

1. Show `situation` as the workplace context and `task` as the question.
2. Render `options` in the order returned as a single-selection radio group
   (label `text`, value `option_id`). Enable Submit once one option is chosen.
3. Submit `{ "selected_option_id": "<option_id>" }`. Do not send `response_text`.
4. Show the feedback sections: `what_worked_well` (why this option may help),
   `trade_offs`, `areas_to_consider` and `skill_to_explore` (may be `null`).
   There is no correct answer, score or result to display.
5. After refresh, `scenario.response.selected_option_id` shows the saved choice.

Written-response activities (`activity_type: "written_response"`, textarea and
`response_text`) are not served in Iteration 2 and do not need a UI yet.

The Your Direction page does not currently offer previous/predicted role
choices; it saves `return_readiness` and `area_to_explore` only. There is no
role-prediction endpoint yet (AI owner), so for now only `source: "previous"`
can be offered from real data.

## 5. Behaviour notes

- **Tokens:** `secrets.token_urlsafe(32)`; only `sha256(token)` stored
  (`anon_session.token_hash`); unknown and malformed tokens get the same `401`;
  each check updates `last_seen_at`.
- **Profile:** one per token; edits replace values and never create a second
  profile; rejected updates leave it unchanged.
- **Practice role:** a `previous` choice is cleared once the saved previous role
  is edited; a `predicted` choice survives profile edits. A `predicted` role is
  checked against the role catalogue only, not against actual model predictions.
- **Sessions:** one active session per token; starting another marks the older
  one `abandoned`. Another token's session always returns the same `404` as a
  missing one.
- **Provider input:** role id and label, years of experience, catalogue skill
  and responsibility labels, duration and difficulty. No token, ids, break
  details or custom skills/responsibilities. Exception: for the `other`
  previous role, `role_label` is the job title the user typed. Feedback
  requests include the scenario's `activity_type`; for MCQs the selected
  option id and text plus every option's text, for written responses the
  response text.
- **Provider output:** validated against `ScenarioContent` / `FeedbackContent`.
  The scenario must be the requested `activity_type`; MCQs need 2-6 options
  with unique ids; written responses have no options. Extra fields (such as
  `is_correct`) and score, pass/fail, correct/incorrect, readiness or
  employability wording are rejected. Calls time out after
  `SCENARIO_PROVIDER_TIMEOUT_SECONDS` (default 10).
- **Activity type:** set in one place, `PRACTICE_ACTIVITY_TYPE` /
  `get_practice_activity_type()` in `app/api/dependencies.py` (`multiple_choice`
  for Iteration 2). Switching it to `written_response` needs no other code change.
- **Answer checks, in order:** session owned by the token (404), scenario in
  the session (404), session active (409), not already answered (409), answer
  field matches the activity type (400 `ACTIVITY_TYPE_MISMATCH`), option
  belongs to the scenario (400 `INVALID_OPTION_ID`). Body errors return 422.
- **Duplicates:** the first answer is kept; any later submission for that
  scenario returns 409 `RESPONSE_ALREADY_SUBMITTED`.
- **Answers** (option ids or text) are stored as data and never executed.

## 6. Tests

```bash
cd backend
venv/bin/python -m pytest -q
```

Result on 2026-09-14: **300 passed, 0 failed** after the multi-activity update (192 before it; baseline before the Iteration 2 backend work:
19 passed, 10 failed because roles/skills are empty without a database `.env`;
`tests/conftest.py` now supplies a fixed test catalogue).

| File | Covers |
|---|---|
| `test_token_access_api.py` | Token format, validation, malformed/unknown tokens, every protected endpoint, returning user, edits without duplication, isolation, hash-only storage, no token in logs |
| `test_profile_update_state.py` | CTM-F-001 regression |
| `test_practice_role_api.py` | Practice role save/retrieve, validation, stale choices, isolation, practice context |
| `test_scenario_provider.py` | Provider contract, curated MCQ and written scenarios, per-option MCQ feedback, stable unique option ids, rejection of scores/judgements, no code execution |
| `test_practice_sessions_api.py` | Session start (MCQ by default, written still available), resume/complete, settings validation, missing context, isolation, provider failure/invalid output/wrong activity type/timeout, minimal provider input |
| `test_scenario_responses_api.py` | Written responses (retained): full token-to-feedback journey, resume, duplicates, validation, wrong answer field, inactive sessions, isolation, feedback failure, no code execution, no response text in logs |
| `test_multiple_choice_responses_api.py` | MCQ journey, feedback per selected option, resume, duplicates, missing/malformed/unknown/other-scenario option ids, written answer rejected, inactive sessions, cross-token isolation, feedback failure and correctness labels, minimal feedback input; service saves the option through the repository |
| `test_practice_activity_contract.py` | Activity-type schemas: MCQ options, submission shape, trade-offs, blocked labels |
| `test_memory_practice_session_repository.py` | Options, selected option and feedback round-trip, copy isolation, owner scoping |

## 7. Known limitations

- In-memory storage (section 8). A token that worked before a restart gets `401`.
- Curated scenarios only (7 scenarios, 3 options each); one scenario per
  session. MCQs are active; written responses are supported but not served. No
  "next activity", coding or drag-and-drop activities or "example approach"
  (AC 4.4.3) yet.
- The feedback backstop rejects the words "correct" and "incorrect", so
  provider feedback that uses "correct" as a verb is treated as unavailable.
- No role-prediction endpoint (AI owner).
- No token expiry policy; no rate limiting (SEC 2.3).
- Free-text caps on existing profile fields not yet added (BE 2.5 / pen-test H-1, H-2).
- Duplicate-submission protection is enforced in the service; a database
  unique constraint on (practice session, scenario) response is recommended.

## 8. Blockers and dependencies

| Blocker | Needs | Owner |
|---|---|---|
| Restart persistence for tokens and profiles | Deployed `anon_session`, `profile`, `profile_skill`, `profile_responsibility` tables and connection details. `profile` foreign keys reference `career_area`, `return_status`, `break_reason`, `experience_option` and `responsibility`, which are unseeded, so writes would fail until those are seeded (DB 2.3). | Database |
| Restart persistence for practice role | Two new `profile` columns: `practice_role_id VARCHAR(64) REFERENCES role(id)` and `practice_role_source VARCHAR(16)` (`previous`/`predicted`) | Database |
| Restart persistence for practice | Tables for practice session (id, owner token hash, role id/label/source, duration, difficulty, status, created/updated/completed timestamps), session scenarios (scenario content, `activity_type`, status), scenario options (`option_id`, `text`, display order; no correctness column), responses (`selected_option_id` and `response_text`, both nullable with exactly one set, `submitted_at`, unique per session + scenario) and feedback (what worked well, trade-offs, areas to consider, skill to explore, feedback status). Shape mirrors `app/repositories/interfaces/practice_session_repository.py`. | Database |
| Production scenario and feedback generation | A `ScenarioProvider` implementation that returns the requested `activity_type` (single-selection MCQs with 2-6 stable, unique option ids for Iteration 2) matching `ScenarioContent`, and MCQ feedback with `trade_offs` matching `FeedbackContent`, plus content guardrails (AI 2.3) | AI |
| Role predictions for Your Direction | A prediction endpoint or service contract | AI |
| API contract sign-off | Review of `API-CONTRACT.md` | Frontend, Database, AI |
| Token expiry | Agreed policy | Team / Security |
| Real token and practice UI | Sections 3 and 4 | Frontend |

## 9. Files changed (all backend)

- **Token and profile:** `app/core/tokens.py` (new), `app/services/session_service.py`, `app/services/profile_service.py`, `app/repositories/interfaces/session_repository.py`, `app/repositories/interfaces/profile_repository.py`, `app/repositories/memory/memory_session_repository.py`, `app/repositories/memory/memory_profile_repository.py`, `app/schemas/anonymous_session.py`, `app/api/routes/anonymous_sessions.py`, `profile.py`, `career_direction.py`, `career_journey.py`, `career_translation.py`
- **Practice role:** `app/schemas/practice_role.py`, `app/services/practice_role_service.py`, `app/api/routes/practice_role.py` (new)
- **Provider:** `app/providers/scenario_provider.py`, `app/providers/curated_scenario_provider.py` (new)
- **Practice:** `app/repositories/interfaces/practice_session_repository.py`, `app/repositories/memory/memory_practice_session_repository.py`, `app/schemas/practice_session.py`, `app/schemas/scenario_response.py`, `app/services/practice_session_service.py`, `app/services/scenario_response_service.py`, `app/api/routes/practice_sessions.py`, `app/api/routes/scenario_responses.py` (new)
- **Wiring and config:** `app/api/dependencies.py`, `app/api/router.py`, `app/core/config.py`
- **Multi-activity (MCQ) update:** `app/providers/scenario_provider.py`, `app/providers/curated_scenario_provider.py`, `app/repositories/interfaces/practice_session_repository.py`, `app/schemas/practice_session.py`, `app/schemas/scenario_response.py`, `app/services/practice_session_service.py`, `app/services/scenario_response_service.py`, `app/api/dependencies.py`; tests `test_practice_activity_contract.py`, `test_multiple_choice_responses_api.py`, `test_memory_practice_session_repository.py` (new), `conftest.py`, `test_scenario_provider.py`, `test_practice_sessions_api.py`, `test_scenario_responses_api.py` (updated)
- **Docs:** `docs/API-CONTRACT.md`, `docs/BACKEND_HANDOVER_ITERATION_2.md`
- **Tests:** `tests/conftest.py`, `test_token_access_api.py`, `test_profile_update_state.py`, `test_practice_role_api.py`, `test_scenario_provider.py`, `test_practice_sessions_api.py`, `test_scenario_responses_api.py` (new); `test_anonymous_sessions_api.py`, `test_memory_session_repository.py` (updated)

No frontend, database schema/seed, AI or security files were changed.

## 10. Next recommended integration steps

1. **Frontend:** apply section 3 steps 1-4 against a local backend
   (`uvicorn app.main:app --reload`) and test generate → save → close tab →
   re-enter token → Career Journey. Then build the practice screens from section 4, with MCQ options as a
   single-selection radio group.
2. **Database:** confirm or create the tables in section 8 and seed the
   catalogue tables so Postgres repositories can be written behind the existing
   interfaces.
3. **AI:** review `app/providers/scenario_provider.py` and implement the provider
   against that contract; swap it in at `get_scenario_provider()` in
   `app/api/dependencies.py`. For Iteration 2 it must return `multiple_choice`
   scenarios when `ScenarioRequest.activity_type` asks for them, never mark an
   option correct, and include `trade_offs` in MCQ feedback.
