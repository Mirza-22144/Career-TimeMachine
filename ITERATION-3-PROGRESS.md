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

**Iteration 2 baseline** `[DONE]`: full onboarding wizard (Your Story → Your Direction) saving against a real backend token; Career Journey with edit/view actions; real predicted-role display; workplace practice (intro → setup → prep → interactive workplace → MCQ activity → reflective feedback → complete), all talking to the real backend with no mock data remaining.

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

### BE 3.1 - Stop passing years_experience/responsibilities to plain MCQ generation

- **Status:** [DONE] **Owner:** Thiri **Date:** 2026-10-04
- **What:** removed `years_experience`/`responsibilities` from `ScenarioRequest` (`app/providers/scenario_provider.py`) and from `PracticeContext`/`build_practice_context()` (`app/services/practice_role_service.py`) entirely - confirmed first that no provider ever actually read either field, so this was dead plumbing, not a behaviour change to anything working today. Removed the now-unused `_label()` helper (its only caller). Updated the `ScenarioRequest(...)` construction site in `practice_session_service.py` and three tests that referenced the removed fields; `test_provider_receives_only_the_career_context_it_needs` now positively asserts both attributes are gone (`not hasattr(...)`) rather than just dropping coverage. All 358 tests pass.
- **Why:** enforces Iteration 3 goal 4's data-usage rule at the one place it could otherwise be silently ignored. `profile.years_experience`/`responsibility_ids` are untouched - this only removes them from the scenario-generation path, not from the profile or from BE 3.3's job comparison.
- **Blocks / Blocked by:** none now. When BE 3.6/BE 3.7 (drag-and-drop, code review) are built, they add their own `years_experience`/`responsibilities` fields to their own request shapes rather than reusing `ScenarioRequest` - see the spec doc Sections 7-8, which already show this.

### BE 3.2 - Job description extraction endpoint

- **Status:** [TODO] **Owner:** TBD **Date:** 2026-10-04
- **What:** `POST /job-descriptions` - local AI extracts structured skills, responsibilities, minimum years of experience and keywords from a user-pasted job description. Treat `raw_text` as untrusted: sanitise, cap length, never let it be interpreted as a model instruction. Full request/response JSON in the spec doc, Section 3.
- **Why:** goal 1 - the entry point for Path 1 (job description analysis), new this iteration.
- **Blocks / Blocked by:** needs the `job_description` table (DB, see spec Section 9.1). Blocks BE 3.3.

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
