# CareerTimeMachine - Team Progress & Change Log

Living document. Everyone updates their own section as they make progress. This is our shared history: what has been done, what is in progress, what is left, and what is blocking who.

## How to use this file (read before editing)

- Find your section (Frontend, Backend, Database, Security, AI). Add your update there.
- Add a new numbered entry at the **top** of your section's log. Never overwrite or delete old entries - this file is our version history.
- Numbering is `AREA <iteration>.<n>`, e.g. `BE 3.1`, `BE 3.2`. Iteration 3 = the `3.x` series.
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
### AREA 3.x - short title

- **Status:** [TODO] **Owner:** name **Date:** YYYY-MM-DD
- **What:** what changed or was built.
- **Why:** the reason / what it enables.
- **Blocks / Blocked by:** who is waiting on this, or what you are waiting on. "none" if standalone.
```

## Iteration 3 goals

Per `CTM_Project_Context_Iteration3_final.docx` (1 Oct 2026) and `CTM_Iteration3_Endpoints_AI_Database_Spec.docx` - read both before starting work, this file tracks progress against them, not the requirements themselves.

1. **Job description analysis (Path 1).** A user pastes a real job advertisement; local AI extracts its requirements and compares them against her full profile (skills, roles, years of experience, responsibilities).
2. **Two AI-predicted roles, with real Australian market data.** Expands Iteration 2's single predicted role to two, each shown with hiring-demand and shortage-status figures sourced from Jobs and Skills Australia.
3. **Personalised roadmap screen.** Skills to build, scenario sequence, recommended certifications and progress, replacing the direct jump from role selection into practice.
4. **Mixed workplace activities, not MCQ-only.** Plain MCQ stays skills/role-driven; two new activity types - code review and drag-and-drop - also use years of experience and responsibilities (team decision, 2026-10-04, refining the context document's blanket rule).
5. **Hybrid MCQ generation.** Pretrained local lookup when every relevant skill is a catalogue skill; a live AI call only when the user has entered a custom (non-catalogue) skill.
6. **Progress dashboard.** Replaces the never-built ePortfolio placeholder; resumable by access token, shows activity without rating or scoring it.
7. **~150 pre-generated skill videos.** Not generated live per user - explicitly out of scope for Iteration 3 per the context document.

## Cross-team blockers (live - keep this current)

| #   | Blocker | Raised by | Needs (owner) | Status |
| --- | ------- | --------- | -------------- | ------ |
| B1  | `role_anzsco_mapping` does not exist yet - CTM's roles are O*NET-based, the Internet Vacancy Index is keyed by ANZSCO/OSCA codes, and the two cannot be joined without this table being populated first. | Backend | Database/data team to source and map | `[TODO]` |
| B2  | Live, per-user AI video generation (discussed earlier) conflicts with the context document, which lists it under "Not part of the current core scope" and specifies ~150 pre-generated videos instead. Needs an explicit team decision before any video work starts, so it isn't built twice in two different directions. | Backend | Team decision | `[TODO]` |
| B3  | Historical snapshot strategy for `role_market_data` not decided - "doubled since her break started" style claims need a fixed comparison period per user, not just the latest data pull. | Backend | Database/data team | `[TODO]` |

---

## Frontend (FE)

**Note on numbering below:** the FE 3.x entries further down this log were written speculatively (2026-10-04) before the real Epics/User Stories/AC document existed, so their numbers don't correspond to actual AC numbers. New entries from here on cite the real AC numbers directly (e.g. "AC 2.3.3") instead.

### AC 3.5.1 / 3.5.2 / 3.4.1 (partial) / 3.1.7 - Remove job description, Clear My Journey, dashboard, profile dropdown

- **Status:** [WIP] **Owner:** Thiri **Date:** 2026-10-08
- **What (backend):** three new endpoints. `DELETE /job-descriptions/{id}` (AC 3.5.1, owner-scoped, 404 for another owner's id). `DELETE /anonymous-sessions/current` (AC 3.5.2) - `SessionService.clear_journey` deletes the profile, every job description and the session; in Postgres the single `anon_session` delete cascades to profile, job_description and practice_session through their existing `ON DELETE CASCADE` keys. `GET /practice-sessions/recent-activities` (AC 3.4.1) - completed scenarios flattened across all of the owner's sessions, newest first, capped at 10. New repository methods: `JobDescriptionRepository.delete_for_owner`, `SessionRepository.delete`, `PracticeSessionRepository.list_for_owner` (memory + Postgres each).
- **What (frontend):** `ProfileMenu.jsx` now shows icon, title and description per item. `CareerJourney.jsx` trimmed to the three profile steps (Skill Relevance Map and Practice Role rows removed), Continue your journey now opens Choose Your Path, and Clear My Journey + `ClearJourneyDialog.jsx` added - on success the local token is forgotten and she lands on Home with Generate / Access Token showing. `Dashboard.jsx` rebuilt as "Your progress": the real empty state ("You haven't started yet."), Recent practice, and saved job descriptions with Remove + confirmation + "Job description removed." toast. Each list loads and fails independently.
- **Not built yet (deliberately, no placeholder data):** chosen roles in "Your roadmaps" and the AC 3.4.2 next-skill card (Practised / Next / Later) - both come from choosing a role on Your Roadmap, which doesn't exist yet, so the top card shows AC 3.4.2's own "Choose a path to build your roadmap." state. View Feedback links and opening a job description's map from the dashboard are also not wired (no feedback-review screen; AC 5.2.1 map not built). Drag and Drop / Code Review never appear in Recent practice because those activity types don't exist in the backend yet.
- **Verification:** 408 backend tests pass (11 new). All three endpoints exercised against the real Postgres: delete took the list from 1 to 0, clear journey returned 204 and the same token then returned 401. Frontend `npm run build` and `npm run lint` clean. **Not clicked through in a browser.**
- **Blocks / Blocked by:** the rest of US 3.4 is blocked by Your Roadmap (AC 2.2.3 / 2.2.4).

### AC 5.1.1 / 5.1.2 - Analyse a Job Description + requirements found

- **Status:** [WIP] **Owner:** Thiri **Date:** 2026-10-08
- **What:** new `screens/AnalyseJobDescription.jsx` at `/analyse-job-description` - one screen moving through paste → analysing → results stages (no separate route for the result; nothing about that transition needs its own URL). Wired to the real `POST /job-descriptions` (`api.createJobDescription`, new `api.js` function with a 30s client-side abort timeout matching AC 5.1.2's exception wording). Results render the real `extracted_skills` (split technical/soft by the response's own `category` field), `extracted_responsibilities`, and `min_years_experience` (card omitted entirely when null, per the dev step "leave out the years heading if the advertisement doesn't state any"). "Compare With My Profile" navigates to a new, deliberately honest placeholder (`screens/JobDescriptionComparison.jsx`) - AC 5.2.1's actual comparison (Bring Back / Worth Refreshing / Transferable Experience / Could Explore) needs new backend reasoning that doesn't exist yet, not simple mock data.
- **Backend fix found along the way:** `JobDescriptionCreate.raw_text` only enforced non-empty (`min_length=1`), not AC 5.1.1's actual 150-character minimum exception - added `MIN_RAW_TEXT_CHARACTERS = 150` to `schemas/job_description.py` plus a new test (`test_create_job_description_rejects_text_under_150_characters`). All 16 job-description backend tests still pass. The 20,000-character max is left as-is (BE 3.2's deliberate choice, matching the AI team's real extraction contract) rather than shrunk to the figma's placeholder "10,000" - the frontend's character counter displays the real 20,000 limit.
- **Why:** goal 1, first half - the actual data-entry point for Path 1.
- **Verification:** genuinely end-to-end against the real GLiNER model and real Postgres (not the memory fallback) - pasted a real job ad, got real extracted output back. Surfaced real, noisy-but-correct model behavior worth knowing about: this model tags some non-technical-sounding phrases ("hybrid", "incident reviews") as `category: "technical"` (flagged to AI team, not fixed - lower priority, needs their judgment on the classification). Also found `min_years_experience` returning `null` for "Three or more years of backend development experience" - a real ad that does state a minimum.
- **`min_years_experience` "or more" fix - applied directly (2026-10-08):** root-caused to `_extract_minimum_experience()`'s regex in `job_description_extractor.py` - pure post-processing on the cleaned text, not something GLiNER itself extracts, so this needed no retraining. The pattern only recognized a number followed directly by `years` (optionally with a `minimum of`/`at least`/`more than`/`over` prefix, or a `N+`/`N-M` suffix) - "N or more years" has no matching shape, so it silently matched nothing. Added one alternative (`\s+or\s+(?:more|above)`) to the existing optional suffix group. Verified standalone (fixes the "or more" case, zero regressions on the 6 previously-working phrasings) and against the real loaded extractor + real model (`min_years_experience` now returns `3` for the example above). Patched both copies that exist in this repo - the live one the backend actually imports (`app/ml/job_description_extraction/job_description_extractor.py`) and the AI team's original handoff copy (`ai/job_description_extraction/job_description_extractor.py`), so a future re-copy from their handoff location doesn't silently reintroduce the bug. All 16 job-description backend tests still pass. AI team notified to mirror the same one-line patch in their own canonical source.
- **Not yet verified in an actual browser** - same limitation as the nav/gating entry above, no browser-automation tool was available this session.
- **Cleanup needed:** another throwaway test row in the real shared Postgres - token `G-gHKzeA1wpcJwR8ozibNQgU7YzqG8UOWXkgOfMW6LM`, job_description_id `4f2573ce3c534dc5b95930cad4d4a35c`. Same Production Reads block as above prevents me from deleting it myself.
- **Blocks / Blocked by:** blocked on AC 5.2.1 (needs new backend profile-comparison reasoning) for `JobDescriptionComparison.jsx` to become real. Not blocked on anything for what's built here.

### AC 3.1.6 / 3.1.7 / 2.3.3 / 3.2.4 - Nav rework, token/profile gating, Choose Your Path, profile confirmation

- **Status:** [WIP] **Owner:** Thiri **Date:** 2026-10-08
- **What:** Top nav now shows Home / Choose Your Path / Practice Scenarios / Dashboard + a profile icon (`components/ProfileMenu.jsx`) with a My Token / Career Profile dropdown, replacing the old Career Journey link and ePortfolio placeholder. Selecting a gated nav item with no active token now opens a dedicated `/access-token-required` page (AC 3.1.6) instead of a dismiss-only modal - `components/TokenRequiredModal.jsx` deleted, no longer used anywhere. Gating also now checks profile completeness, not just token presence (`useAccessTokenFlow.attemptTokenGate`, `requireProfile` option): an active token with an unconfirmed profile is redirected into the wizard at the first unfinished step via the existing `getResumeStep()`, applied to Choose Your Path, Practice Scenarios and Dashboard. New `screens/ChooseYourPath.jsx` (AC 2.3.3) replaces Your Direction as the post-profile fork (Analyse a Job Description / Explore Roles); it also guards itself directly on `profile.confirmed` on mount, not only via the nav click, so a bookmarked/back-navigated visit can't bypass the rule. New `components/SaveProfileDialog.jsx` + `screens/ProfileSetUp.jsx` implement AC 3.2.4 - "Save your career profile?" now shown once, the first time only (gated on the existing `isEditReturn` flag, which already distinguished first-time completion from an edit-return), before showing a real summary (role, years, skills, responsibilities count, break years) read back from the just-saved profile. `screens/Dashboard.jsx` is a deliberately honest placeholder - the nav item and both gating rules are real, but US 3.4's actual dashboard content is a separate, not-yet-built story.
- **Why:** goal/scope per the real Epics/User Stories/AC document (not the earlier speculative FE 3.x list) - these four ACs are the foundational nav/routing change every other Iteration 3 screen depends on.
- **Verification:** `npm run build` and `npm run lint` both clean. No mock data - `ProfileSetUp.jsx` reads the real `GET /profile` + catalogue endpoints back after a real `PATCH /profile` + `POST /profile/confirm` against the live backend, confirmed field-by-field (role label, years label, skill labels, break years) against real responses from the real Postgres instance. **Not yet verified in an actual browser** - no browser-automation tool was available in this session to click through the UI, so this is unverified for visual/interaction correctness (modal positioning, dropdown focus handling, etc.) even though the underlying data wiring is confirmed real. Please click through before relying on it.
- **Cleanup needed:** a throwaway anonymous session (role: Software Developer, skills: Java/Python/SQL/Looker, break 2021→2026, confirmed) was created against the real shared Postgres at `34.56.117.131` while verifying this - my own tooling blocked me from deleting it directly (Production Reads). Token: `X2cd-utTwjLMgEy1kRIpCZeHGj9Atkj3gBhAac3iBug` - needs manual cleanup.
- **Blocks / Blocked by:** blocks FE work on the job-description path (AC 5.1.x/5.2.x, routes to `/analyse-job-description`) and the roadmap (AC 2.2.3/2.2.4/2.4.1, routes to `/your-roadmap`) - both are linked from Choose Your Path but not built yet. `/skill-relevance-map` and `/your-direction` are still registered in the router and still work, left in place until Your Roadmap is ready to replace them (removing them now would strand CareerJourney's Edit links).

### FE 3.1 - Path hub screen

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** new screen reached right after profile setup (Step 1) offering "Analyse a job description" (Path 1) and "Explore roles and practise" (Path 2) side by side - neither forced, no dismiss-a-prompt pattern. Reachable again later from the dashboard (FE 3.12), since she'll keep finding new job ads over the weeks she uses CTM.
- **Why:** the fork point the whole updated Iteration 3 journey branches from.
- **Blocks / Blocked by:** none to start - a routing screen, doesn't depend on backend work existing first.

### FE 3.2 - Paste-a-job-description screen + extracted requirements display

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** text area for pasting a real job description, calling `POST /job-descriptions` (BE 3.2). Shows the extracted skills/responsibilities/experience requirement back to her before the comparison step runs, so a bad extraction is visible rather than silently trusted.
- **Why:** goal 1 - the actual data-entry point for Path 1.
- **Blocks / Blocked by:** blocked by BE 3.2.

### FE 3.3 - Profile-vs-job comparison display

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** renders BE 3.3's four groups (existing alignment / transferable / worth refreshing / worth exploring) with supportive, never-pass/fail wording. Handles the "close match" case specially - leads with "While You Were Away" content (FE 3.7) rather than an empty explore list, per the context document's explicit guidance for what it calls the most common case, not an edge case.
- **Why:** goal 1 - where she actually reads what the comparison means for her.
- **Blocks / Blocked by:** blocked by BE 3.3.

### FE 3.4 - Skill relevance map, updated for two paths

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** one component serves both paths - 4 groups on Path 1 (from the pasted job description), 2 groups on Path 2 (from the selected role's O*NET skills). No counts, percentages or coverage figures anywhere - it describes the role, not the user. Keeps "commonly listed for this role" (O*NET) and "in demand" (Jobs and Skills Australia only) strictly separate in the copy.
- **Why:** the one screen every journey passes through regardless of path chosen.
- **Blocks / Blocked by:** Path 1 half blocked by FE 3.3; Path 2 half can be built now against the existing role/skill catalogue.

### FE 3.5 - Two predicted roles with market data

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** replaces the current single predicted-role card with two role cards, each showing hiring-demand text and shortage status, source and date shown on every figure - never invented or rounded beyond what the data actually says.
- **Why:** goal 2.
- **Blocks / Blocked by:** blocked by BE 3.4, which is itself blocked by B1/B3.

### FE 3.6 - Personalised roadmap screen

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** new screen - skills she has / worth refreshing / worth exploring, relevant workplace practices, a recommended sequence, and the scenarios that help her practise. Explicitly not "Course 1 -> Course 2 -> Certification 3" - answers what to explore next given where she already is.
- **Why:** goal 3.
- **Blocks / Blocked by:** needs a backend read/write endpoint over the `roadmap` table (spec Section 9.5) - not yet logged as a BE card; add one when this is picked up.

### FE 3.7 - "While You Were Away"

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** industry-change context for the user's selected role/occupation over her career-break dates - still relevant / changed / worth investigating, each claim tied to a real dataset, never an invented trend.
- **Why:** context goal - also doubles as the lead content for a close job-description match (FE 3.3).
- **Blocks / Blocked by:** needs a backend endpoint for this - not yet scoped/logged as a BE card.

### FE 3.8 - Mixed activity types in workplace practice

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** the activity screen needs to render whichever activity type the session returns - workplace MCQ, technical MCQ, drag-and-drop or code review - not one fixed layout. Needs a loading/timeout state for the hybrid live-MCQ path (BE 3.5) specifically, since that call can have real latency unlike the pretrained path.
- **Why:** goal 4/5 - the "MCQ only doesn't test real skills" complaint, the most-requested change from Iteration 2 feedback alongside hotspot discoverability (already fixed).
- **Blocks / Blocked by:** blocked by BE 3.5 for the loading state; the type-switch itself can be scaffolded now against mocked responses.

### FE 3.9 - Code review activity UI

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** code snippet display (syntax-highlighted) plus option selection for the error category. Never shows a right/wrong badge - reflective feedback only, matching the backend-only `correct_option_id` decision (BE 3.6, confirmed).
- **Why:** goal 4, second new activity type.
- **Blocks / Blocked by:** blocked by BE 3.6.

### FE 3.10 - Drag-and-drop activity UI

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** sentence template with 3 drop targets and 5 draggable option chips. Every option gets feedback on selection, framed as improvement to make, never marked wrong.
- **Why:** goal 4, third new activity type.
- **Blocks / Blocked by:** blocked by BE 3.7.

### FE 3.11 - Pre-generated skill video + post-video question

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** after a scenario, show the relevant short skill video (matched by the actual skill used, not a generic library), then one reflective question to check understanding - never graded pass/fail, consistent with the rest of the product. No live video-generation call anywhere in the frontend.
- **Why:** goal 7.
- **Blocks / Blocked by:** needs `skill_video` rows to actually exist (DB, spec Section 9.6) before this can be tested with real content, not just mocks.

### FE 3.12 - Progress dashboard (replaces the ePortfolio placeholder)

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** one place showing saved profile, added job descriptions, roles explored, roadmap position, completed scenarios with their feedback, and videos watched. Resumes via access token. Describes activity, never rates it - no totals, streaks or completion percentages anywhere on this screen.
- **Why:** goal 6 - the nav tab already relabelled from ePortfolio (earlier team decision) finally gets real content.
- **Blocks / Blocked by:** blocked by BE 3.8, and in practice by most of the above existing first, since it surfaces their data.

---

## Backend (BE)

**Iteration 2 baseline** `[DONE]`: layered FastAPI (routes / schemas / services / repositories / interfaces). Anonymous sessions, profile capture/confirm, practice role, Postgres-backed practice sessions (session-scoped keys, fixed 2026-09-18 after a real cross-session collision bug), real role prediction (one role), AI-pool reflective MCQ scenarios (81 scenarios, 27 roles × 3 difficulties), rate limiting, input caps, security logging. All 358 tests passing as of the last Iteration 2 deploy.

### BE 3.11 - Vacancy counts shown as a rounded range, never an exact number

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-10-07
- **What:** per the industry mentor's guidance, `/predicted-roles` no longer exposes an exact ad count anywhere. New `app/core/vacancy_rounding.py::round_to_range()` - bucket width scales with magnitude (nearest 10 under 100, nearest 50 under 1,000, nearest 100 under 10,000, nearest 500 above), so a small-count role and a large-count role both get a proportionally meaningful band instead of one fixed width for everyone. Applied at the service layer (`RolePredictionService._market_data_for`/`_to_display`), not the repository - the repository still returns exact `RoleMarketData` (honest raw data access), and the rounding happens as a presentation step on top of it, same separation already used elsewhere in this backend.
- **Also switched the input from `ads_latest` to `ads_12m_avg`** (team decision, this session): the 12-month average is more representative than a single month's snapshot, and - more importantly - it's the same basis `yoy_change_pct` is already computed from, so the count and the trend line are no longer drawn from two different ideas of "the number." `ads_latest` is no longer in the API response at all.
- **Schema change**: `MarketDataResponse.ads_latest`/`ads_12m_avg` (exact ints) replaced with `ads_range_low`/`ads_range_high` (two plain ints, not a pre-formatted string, so the frontend controls display formatting/locale).
- 14 new tests (12 for the rounding function's boundaries including the exact real Database Administrator figures from BE 3.10's verification, plus the existing market-data test updated for the new shape). Verified live again against a real, fully-seeded Postgres (same data as BE 3.10's run): response now shows `"ads_range_low": 1700, "ads_range_high": 1800"` with no exact figure anywhere in the payload. All 395 tests pass.
- **Why:** direct instruction from the industry mentor - an exact figure implies more precision than the underlying data (or the role-to-ANZSCO mapping) can actually support.
- **Blocks / Blocked by:** none - builds on BE 3.10, no other card depends on this specific presentation detail.

### BE 3.10 - Two predicted roles with real market data

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-10-07
- **What:** new `GET /predicted-roles` (plural), additive alongside the existing `GET /predicted-role` (singular) - that endpoint is untouched and still live for the current frontend until it switches over (FE 3.5). Wired to AI 3.2's real Version 2 two-role model (moved `career_role_predictor_v2.py`/`career_role_recommender_v2_bundle.joblib` from `backend/ai/` into `app/ml/`, same Dockerfile-only-copies-`app/` reasoning as BE 3.9). New `TwoRolePredictionProvider` interface (mirrors `RolePredictionProvider`, reuses the same `RolePredictionRequest`/`SkillContext` - the request shape is identical, only the response differs) and the real `MLTwoRolePredictionProvider` adapter. Each predicted role is enriched with real Australian hiring-demand data by reading DB 3.1's `role_vacancy_latest` view (new `VacancyRepository` interface + Postgres/Memory implementations) - `market_data` is `None` for a role with no ANZSCO mapping yet (e.g. `other`), never fabricated. Extended the existing `RolePredictionService` rather than duplicating its profile/skill-context logic (both new dependencies are optional constructor params, so the existing single-role construction site is unaffected). 9 new tests, including one that injects real market data via `MemoryVacancyRepository` and one confirming the singular endpoint is unaffected; all 381 tests pass.
- **Verified end to end against a real local Postgres loaded with the data team's actual seed data** (real roles/skills catalogue, real `anzsco_occupation`/`role_anzsco_map`/`vacancy_monthly`), not just the in-memory test suite: a real profile (`database_administrator`) through a real HTTP request returned two real, distinct predicted roles, both correctly enriched with real ad counts, a real year-on-year change figure, and the real ANZSCO title/confidence - and it happened to surface DB 3.1's documented "shared ANZSCO group" case live (both predicted roles mapped to the same group, correctly showing identical real figures rather than two different fabricated ones).
- **Why:** goal 2 - matches the context document's "2 AI-predicted roles" requirement, now with real hiring-demand data behind it instead of a placeholder.
- **Blocks / Blocked by:** none - was blocked by B1 (role-ANZSCO mapping), resolved by DB 3.1. Still open, not a blocker: shortage status (Occupation Shortage List) isn't loaded yet per DB 3.1's own note, so this endpoint only returns ad-volume/trend data, not shortage flags - the schema (`MarketDataResponse`) has room to add it later without a breaking change. Unblocks FE 3.5 (frontend still reads the singular endpoint today).

### BE 3.9 - Job description extraction verified against the real model end to end

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-10-06
- **What:** placed the real `gliner_small_v2_5` model (downloaded from the AI team's Google Drive link, moved from its Google-Drive-export double-nested folder into `backend/models/gliner_small_v2_5/` - the path `JOB_DESCRIPTION_MODEL_DIR` already expected) and installed the AI team's exact pinned dependencies (`torch==2.11.0+cpu`, `transformers==5.16.1`, `gliner==0.2.29`, `rapidfuzz==3.14.6`, `pydantic` bumped 2.13.4→2.13.5). Ran a real extraction end to end through our own provider code (not a mock) against a sample job description - correctly identified Python/SQL/AWS as technical skills, Communication/Collaboration as soft skills, real responsibilities, a 3-year minimum, and "Data Engineer" as the role title. Model loads in ~7s, extraction itself runs in ~0.6s.
- **Real issue found and fixed during this**: the GLiNER model's own config references `microsoft/deberta-v3-small` as its base encoder (`encoder_config: null` in `gliner_config.json`), which it tries to resolve from Hugging Face Hub separately from the local model folder, even with `local_files_only=True` - this fails on any machine that has never loaded it before, with no internet available at that moment. Resolved by allowing one brief network call to seed the local Hugging Face cache (downloads a 9KB `config.json`, not model weights) - fully offline afterward. **Correction to the AI team's `MODEL_DEPLOYMENT.md`**: its claim "does not need network access to Hugging Face after the container has been built" is not quite accurate as currently packaged - the very first load on a fresh machine/container needs one tiny network call unless that 9KB cache entry is also pre-baked into the deployment image. Worth feeding back to them, and worth baking that cache file into the Cloud Run image alongside the model itself when this actually gets deployed.
- **Also fixed a real design issue this surfaced**: `dependencies.py` was constructing the real provider eagerly at import time, which meant the whole app (and every test run) would try to load the 1.3GB model the moment the model folder existed locally - slow, and a single transient load failure would have broken everything, not just this one feature. Changed to lazy, thread-safe, cache-on-first-use construction (`get_job_description_extraction_provider()`), with a try/except around real-provider construction that falls back to the clean "unavailable" provider (logged loudly) rather than crashing. Also fixed `test_create_job_description_fails_without_a_real_model_configured`, which had been silently relying on the model's absence as ambient local-machine state rather than asserting it explicitly - it now uses `use_job_description_provider` like every other test. Added a new `test_create_job_description_with_the_real_model`, skipped automatically wherever the real model isn't present (so CI and other developers' machines are unaffected), so this real integration stays checked going forward. All 372 tests pass (was 371).
- **Why:** the user asked for the whole job-description feature working end to end, not just the graceful-fallback path - this is that confirmation, plus two real bugs this exercise would otherwise have shipped silently.
- **Blocks / Blocked by:** none for local dev. For actual deployment: `backend/requirements.txt` now has the heavy deps (this was the deliberately-deferred item from BE 3.2); the Dockerfile's install step needed `--extra-index-url https://download.pytorch.org/whl/cpu` added, since `torch==2.11.0+cpu` isn't on plain PyPI - done. Still open: bake the 9KB `deberta-v3-small` config cache into the deployment image too, and confirm Cloud Run's ≥2GiB memory recommendation from `MODEL_DEPLOYMENT.md` before actually deploying this.

### BE 3.1 - Stop passing years_experience/responsibilities to plain MCQ generation

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-10-04
- **What:** removed `years_experience`/`responsibilities` from `ScenarioRequest` (`app/providers/scenario_provider.py`) and from `PracticeContext`/`build_practice_context()` (`app/services/practice_role_service.py`) entirely - confirmed first that no provider ever actually read either field, so this was dead plumbing, not a behaviour change to anything working today. Removed the now-unused `_label()` helper (its only caller). Updated the `ScenarioRequest(...)` construction site in `practice_session_service.py` and three tests that referenced the removed fields; `test_provider_receives_only_the_career_context_it_needs` now positively asserts both attributes are gone (`not hasattr(...)`) rather than just dropping coverage. All 358 tests pass.
- **Why:** enforces Iteration 3 goal 4's data-usage rule at the one place it could otherwise be silently ignored. `profile.years_experience`/`responsibility_ids` are untouched - this only removes them from the scenario-generation path, not from the profile or from BE 3.3's job comparison.
- **Blocks / Blocked by:** none now. When BE 3.6/BE 3.7 (drag-and-drop, code review) are built, they add their own `years_experience`/`responsibilities` fields to their own request shapes rather than reusing `ScenarioRequest` - see the spec doc Sections 7-8, which already show this.

### BE 3.2 - Job description extraction endpoint

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-10-05
- **What:** built the full layered path for `POST /job-descriptions` (plus `GET /job-descriptions` and `GET /job-descriptions/{id}`), wired to AI 3.1's real GLiNER extractor. New `job_description` table (migration applied and verified against a disposable local Postgres instance, including the real `PostgresJobDescriptionRepository` round-tripping through it - not just the raw SQL). New `JobDescriptionExtractionProvider` interface (mirrors `RolePredictionProvider`), with the real `GlinerJobDescriptionExtractionProvider` and a fallback `UnavailableJobDescriptionExtractionProvider` that fails cleanly (503) rather than fabricating results. Moved the AI team's runtime module and skill catalogue from `backend/ai/job_description_extraction/` into `app/ml/job_description_extraction/` - the Dockerfile only copies `app/`, same lesson as `BE 2.14`'s role-prediction handover, or this would have been silently missing from the deployed image. The real provider's heavy imports (`gliner`/`torch`/`transformers`) happen lazily inside `__init__`, never at module level, and `dependencies.py` only constructs it when `HAS_JOB_DESCRIPTION_MODEL` finds the ~1.3GB model directory actually present on disk - a fresh checkout or the test suite never needs those packages installed. `raw_text` capped at 20,000 characters (matching the AI team's own contract), request schema rejects unknown fields, provider calls run through a timeout exactly like `ScenarioProvider`'s `call_provider`. 13 new tests (auth, validation, provider-down, provider-timeout-shaped failure, invalid-output rejection, cross-owner isolation, list ordering); all 371 backend tests pass.
- **Why:** goal 1 - the entry point for Path 1 (job description analysis), and the first Iteration 3 feature with a real AI deliverable wired all the way through to the database.
- **Blocks / Blocked by:** unblocks BE 3.3 (profile-vs-job comparison), which can now read real stored job descriptions. One open item, not a blocker: `backend/requirements.txt` has **not** been updated with `torch`/`transformers`/`gliner`/`rapidfuzz` yet - deliberately held back, since adding them makes every `pip install` meaningfully heavier for the whole team immediately, even though nothing needs them until the real model is actually deployed somewhere. Add them when ready to deploy this for real (Cloud Run needs ≥2GiB memory per `MODEL_DEPLOYMENT.md`).

### BE 3.3 - Profile-vs-job comparison endpoint

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** `POST /job-descriptions/{job_description_id}/compare` - the only place in the whole product where years of experience and responsibilities are compared against something, per the context document's explicit rule. Groups results into existing alignment / transferable / worth refreshing / worth exploring. Wording must never read as pass/fail - see the spec doc, Section 4, for the required supportive phrasing.
- **Why:** goal 1, second half - turns the extracted job requirements (BE 3.2) into something the user can actually read against her own profile.
- **Blocks / Blocked by:** depends on BE 3.2. Needs `job_description_comparison` table (DB, see spec Section 9.2).

### BE 3.4 - Expand role prediction to 2 roles + market data

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** change `GET /predicted-role` (singular) to `GET /predicted-roles`, returning two roles instead of one - breaking change to the current `RolePredictionProvider` interface, which only returns one `PredictedRoleContent` today. Backend then enriches each role with hiring-demand/shortage data from `role_market_data` (a lookup, not an AI call). Full contract in the spec doc, Section 5.
- **Why:** goal 2 - matches the context document's explicit "2 AI-predicted roles" requirement (Iteration 2 shipped one).
- **Blocks / Blocked by:** blocked by B1 (`role_anzsco_mapping`) and B3 (snapshot strategy) for the market-data half; the role-count change itself is not blocked.

### BE 3.5 - Hybrid MCQ generation (pretrained + live)

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** backend routing decision, not an AI decision - if every skill relevant to the activity is a catalogue `skill_id`, use the existing local pretrained lookup (unchanged from Iteration 2); if the user has a relevant `custom_skill` (free text, not in the catalogue), call the AI service live instead. Needs a loading state and timeout/fallback on the frontend for the live path. Full routing table and both request shapes in the spec doc, Section 6.
- **Why:** lets MCQ generation actually cover skills the catalogue doesn't have, without making every request pay live-AI latency.
- **Blocks / Blocked by:** plain MCQ itself does not change its skills+role-only input (goal 4 only applies to the two new activity types above).

### BE 3.6 - Code review activity type

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** new `ActivityType` value `code_review`. User sees a code snippet and picks the error category (syntax error, null/attribute error, etc.). Confirmed exception to the "no option marked correct" rule: `correct_option_id` is backend-only, used to select feedback text, never shown as right/wrong in the UI. Full contract in the spec doc, Section 7.
- **Why:** the other new activity type from goal 4 - code review and reasoning only, no execution/sandboxing, matching the context document's explicit scope boundary.
- **Blocks / Blocked by:** needs `practice_scenario.code_snippet`/`language` columns (DB, see spec Section 9.8).

### BE 3.7 - Drag-and-drop activity type

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** new `ActivityType` value `drag_and_drop`. Sentence template with 3 blanks, 5 options (3 correct, 2 distractors), constructive feedback on every option - never "wrong". Uses skills, role, years of experience and responsibilities (team decision, see Iteration 3 goal 4). Full request/response JSON in the spec doc, Section 8.
- **Why:** one of the two new activity types replacing "MCQ only" as the sole interaction type, per Iteration 2 feedback's most-repeated workplace complaint.
- **Blocks / Blocked by:** needs `practice_scenario.sentence_template` and `practice_scenario_option.fits_blank_id` columns (DB, see spec Section 9.8/9.9).

### BE 3.8 - Progress dashboard / resume endpoint

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** new endpoint(s) returning the full dashboard view for Step 12 - saved profile, job descriptions added, roles explored, roadmap position, completed scenarios with their feedback, videos watched. Describes activity, never rates it (no totals, percentages, streaks).
- **Why:** replaces the never-built ePortfolio placeholder; lets a user leave mid-session and resume exactly where she stopped.
- **Blocks / Blocked by:** depends on BE 3.2-3.7 existing first, since the dashboard surfaces their data. See spec Section 9.7 (`dashboard_state`) for whether a dedicated table is even needed.

---

## Database (DB)

**Iteration 2 baseline** `[DONE]`: `anon_session`, `profile` (+ skill/responsibility junctions), `role`, `skill`, `practice_session`, `practice_scenario`, `practice_scenario_option` (session-scoped keys since the 2026-09-18 fix) all live in Postgres. `career_area`/`break_reason` retired/unused, not dropped.

### DB 3.1 - Role-to-ANZSCO mapping and Australian job ad volumes

- **Status:** [DONE] **Owner:** Devang **Date:** 2026-10-07
- **What:** built and loaded three tables and one view in Cloud SQL. `anzsco_occupation` (10 ANZSCO 4-digit groups); `role_anzsco_map` (27 rows: each O*NET-based role mapped by hand to one ANZSCO group, with a high/medium/low confidence and a written rationale - 12 high, 8 medium, 7 low; `other` unmapped); `vacancy_monthly` (22,140 rows of JSA Internet Vacancy Index ad counts, August 2026 release, CC BY 4.0 - 10 groups x 9 regions (AUST + 8 states/territories) x March 2006 to August 2026, 3-month rolling averages). View `role_vacancy_latest` returns `ads_latest`, `ads_12m_avg`, `yoy_change_pct` and `latest_month` per role per state for the newest month loaded. Pipeline `data/pipeline/build_vacancy_seed.py` validates the source (0 suppressed values in our groups; states reconcile to AUST within 0.67 ads) and writes rerun-safe seed files; load verified with `data/schema/verify_vacancy.sql`.
- **How to read it:** `SELECT ... FROM role_vacancy_latest WHERE role_id = %s AND state = 'AUST'`. Several roles share one ANZSCO group and so show the same figure (Software Developer, Computer Programmer and Blockchain Engineer all show 2,896), so the UI must label the number with `anzsco_title` and `latest_month`, never as ads for her exact role. Figures are online job ads (SEEK, CareerOne, Workforce Australia), not jobs or hires.
- **Why:** resolves B1 - O*NET roles can now be joined to Australian vacancy data. The full monthly history also gives B3 a basis: a "since her break started" comparison can read the month her break began from `vacancy_monthly`, not just the latest pull.
- **Blocks / Blocked by:** unblocks the market-data half of BE 3.4 and FE 3.5. Differences from spec Section 9: the table is `role_anzsco_map` (spec says `role_anzsco_mapping`), and demand comes from `vacancy_monthly` plus the view rather than a `role_market_data` table. Shortage status is not loaded yet (needs the JSA Occupation Shortage List). Monthly refresh: download the new IVI file, rerun the script, rerun `seed_vacancy_monthly.sql`.

*No Iteration 3 entries yet. See `CTM_Iteration3_Endpoints_AI_Database_Spec.docx` Section 9 for the full new-table specification (`job_description`, `job_description_comparison`, `role_anzsco_mapping`, `role_market_data`, `roadmap`, `skill_video`, `dashboard_state`) and the changes needed on `practice_scenario`/`practice_scenario_option` - add your entries above this line once you start building from it.*

---

## Security (SEC)

**Iteration 2 baseline**: 1 confirmed vulnerability fixed and verified, rate limiting and input caps shipped, security/startup-mode logging in place. Still open from Iteration 2: security headers (H-3), `/docs` exposure policy decision, full threat-model of the AI/auth surfaces.

*No Iteration 3 entries yet. New trust boundaries this iteration worth a threat-model pass once built: pasted job-description text (untrusted input, prompt-injection risk - see spec doc Section 10), the live AI call path for custom-skill MCQ generation, and the longer-lived access token now guarding a multi-week dashboard journey.*

---

## AI (AI)

**Iteration 2 baseline** `[DONE]`: trained role-prediction classifier (one role) and the 81-scenario reflective MCQ dataset, both running in-process, no external API.

### AI 3.1 - Local job-description requirement extraction

- **Status:** [DONE] **Owner:** Orkhan **Date:** 2026-10-05
- **What:** I developed and evaluated a local job-description extraction component using `gliner-community/gliner_small-v2.5`, catalogue matching and deterministic Python validation. It accepts untrusted job-advert text and returns exactly five fields: skills, responsibilities, minimum years of experience, keywords and a role-title estimate. The handover includes the standalone Python module, the 1,299-skill catalogue, request and response examples, the integration contract, evaluation evidence, robustness evidence and deployment instructions.
- **Evidence:** On an independent ten-advert holdout set, technical-skill F1 was 0.7723, soft-skill F1 was 0.8980 and responsibility F1 was 0.7917. Minimum-experience and role-title exact-match accuracy were both 100%, and the schema pass rate was 100%. The corrected extractor passed 13/13 robustness tests and the standalone deployment version achieved functional equivalence on 11/11 tested outputs.
- **Why:** supports Iteration 3 goal 1 by converting an unstructured job advertisement into structured requirements that the backend can compare with the user’s profile.
- **Blocks / Blocked by:** the AI extraction component is complete and unblocks BE 3.2. Backend integration still requires the endpoint and database work. The 1.28 GB model weights are deliberately excluded from Git and must be supplied during container deployment or retrieved from approved cloud storage, as documented in `MODEL_DEPLOYMENT.md`.

### AI 3.2 - Two-role career recommender Version 2

- **Status:** [DONE] **Owner:** Orkhan **Date:** 2026-10-05
- **What:** I upgraded the career-role recommender to return two distinct future IT roles instead of one. The Version 2 pipeline uses TF-IDF text features, a tuned LinearSVC classifier and hybrid ranking based on the trained model, selected-skill fit and current-role similarity. It excludes the user’s current role and the internal `Other` class from both recommendations.
- **Evidence:** The locked model achieved 85.28% accuracy, 68.46% balanced accuracy, 67.48% macro F1 across all 27 roles, 93.85% top-two accuracy and 96.52% top-three accuracy on the protected real test partition. The corrected recommender passed 8/8 backend integration tests. Its catalogue-profile audit improved intended-role top-two coverage from 5/27 to 20/27.
- **Why:** delivers the AI portion of Iteration 3 goal 2 and gives users two credible directions instead of presenting one recommendation as the only possible path.
- **Blocks / Blocked by:** the standalone model and two-role response contract are complete. BE 3.4 must connect the provider to `GET /predicted-roles`. Market-demand and shortage information remains a separate database lookup and is blocked by the role-to-ANZSCO mapping and historical snapshot decisions.

### AI 3.3 - Iteration 3 workplace-activity content

- **Status:** [TODO] **Owner:** Orkhan **Date:** 2026-10-05
- **What:** the validated Iteration 2 dataset of 81 reflective scenarios remains available as the current baseline. Iteration 3 generation and revision work has not started because job-description extraction was prioritised first. New MCQ, code-review and drag-and-drop content will be produced only after the final backend contracts and required record counts are confirmed.
- **Why:** records the current boundary clearly and avoids generating content against an outdated or assumed backend schema.
- **Blocks / Blocked by:** awaiting confirmation of the final BE 3.5, BE 3.6 and BE 3.7 content contracts, generation quantities and live-AI fallback requirements.
