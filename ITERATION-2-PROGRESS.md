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
- **Status:** [TODO]  **Owner:** name  **Date:** YYYY-MM-DD
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

| # | Blocker | Raised by | Needs (owner) | Status |
|---|---|---|---|---|
| B1 | LLM output format (the exact JSON shape a scenario comes back as) is not yet agreed, so backend cannot build the scenario endpoints and frontend cannot build the scenario screen against a real contract | Backend | AI to define and agree the scenario request/response contract | `[BLOCKED]` open |
| B2 | Sessions and profiles are still in-memory (lost on restart), so user progress cannot be persisted yet | Backend | Database to provide profile/session/progress tables + connection details | `[BLOCKED]` open |
| B3 | Sign-on method for Iteration 2 not finalised (token generation now, TOTP later) - affects the frontend sign-on screen and the security design | Security | Team decision, then Security to spec the token flow | `[WIP]` open |

---

## Frontend (FE)

**Iteration 1 baseline** `[DONE]`: cards 1-7 UI (Get Started, Previous IT Experience, Skills & Experience, Career Break, Review Profile, Skills & Industry Relevance, Skill/Industry detail). Talks to the API using the `X-Session-Token` header, hash-based routing.

### FE 2.1 - Workplace Scenarios screen
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** new screen that requests a personalised scenario, shows the question(s), lets the user answer, and shows the result.
- **Why:** the core Iteration 2 user-facing feature.
- **Blocks / Blocked by:** blocked by B1 (needs the agreed LLM scenario contract) and BE 2.1.

### FE 2.2 - Progress / resume UI
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** show which scenarios are done vs remaining; resume from where the user left off.
- **Why:** goal 2 - returning users continue rather than repeat.
- **Blocks / Blocked by:** blocked by BE 2.2 (progress endpoints) and B2.

### FE 2.3 - Sign-on screen (placeholder)
- **Status:** [DONE]  **Owner:** Thiri  **Date:** 2026-09-13
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

### FE 2.4 - Robustness + security hardening (frontend)
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** add an error boundary so a failed API call does not white-screen the app (seen during the pen test); add SRI `integrity` on the Google Fonts link (pen-test H-5); help add security headers at build/host level (H-3).
- **Why:** reliability + close pen-test hardening items.
- **Blocks / Blocked by:** coordinate with SEC 2.2.

---

## Backend (BE)

**Iteration 1 baseline** `[DONE]`: layered FastAPI (routes / schemas / services / repositories / interfaces). Anonymous sessions, catalogue endpoints, profile capture + confirm + delete, career journey, career translation, career direction, unified error envelope. All behind repository interfaces so storage can be swapped.

### BE 2.1 - Workplace Scenario endpoints
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** endpoints to generate a scenario for the current user (calls the AI service) and to submit/return an answer result. The AI call sits behind a new repository/service interface, same pattern as the existing code.
- **Why:** serves the Workplace Scenarios feature.
- **Blocks / Blocked by:** blocked by B1 (LLM contract). Blocks FE 2.1.

### BE 2.2 - Progress persistence endpoints
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** save and fetch a user's scenario progress (completed scenarios, answers, timestamps).
- **Why:** goal 2 - resume, no repeats.
- **Blocks / Blocked by:** blocked by B2 (DB tables). Blocks FE 2.2.

### BE 2.3 - Token generation for sign-on
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** implement the token-generation sign-on flow for this iteration (kept swappable so a TOTP authenticator can replace/augment it in Iteration 3).
- **Why:** goal 3.
- **Blocks / Blocked by:** blocked by B3 (design decision from Security).

### BE 2.4 - Fix CTM-F-001 (broken atomicity on PATCH /profile)
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** reorder `ProfileService.update_profile()` so all validation (including the date-order rule) runs before any `setattr()` on the stored profile - or have the repository return a defensive copy and only commit in `save()`. Add a regression test (repeat pen-test CTM-PT-005b). Re-check `PATCH /career-direction` stays clean.
- **Why:** fixes the one confirmed pen-test vulnerability (integrity issue: a rejected update still partly saved).
- **Blocks / Blocked by:** pair with SEC 2.1.

### BE 2.5 - Input caps (hardening)
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** add `max_length` on free-text fields (H-1) and a max list size (H-2) in the Pydantic schemas.
- **Why:** storage hygiene and abuse resistance before the DB goes live.
- **Blocks / Blocked by:** none.

---

## Database (DB)

**Iteration 1 baseline** `[DONE]`: `role`, `skill`, `role_skill` tables live in Postgres and drive roles/skills. Other catalogue lists still come from in-memory placeholders. Sessions and profiles are **not** persisted (in-memory only).

### DB 2.1 - Persist sessions and profiles
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** create tables for anonymous sessions and profiles matching the backend's data model; provide connection details for the backend `.env`.
- **Why:** without this, all user state is lost on restart - blocks progress saving.
- **Blocks / Blocked by:** blocks B2, BE 2.2.

### DB 2.2 - Progress storage
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** table(s) for scenario progress (which scenarios a user has done, their answers/results, timestamps).
- **Why:** goal 2 - resume / no repeats.
- **Blocks / Blocked by:** blocks BE 2.2. Coordinate the shape with AI (scenario ids).

### DB 2.3 - Seed remaining catalogue tables
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** fill the responsibilities, break-reasons, return-statuses and career-areas tables (currently placeholder-only) with real data; keep ids stable.
- **Why:** removes the in-memory placeholder fallback.
- **Blocks / Blocked by:** none.

### DB 2.4 - Startup mode indicator (pen-test R09)
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** make the app log at startup whether it is using the database or the in-memory fallback.
- **Why:** the pen test flagged silent fallback to mock data as a risk.
- **Blocks / Blocked by:** small, do with backend.

---

## Security (SEC)

**Iteration 1 baseline** `[DONE]`: full pen test (local) + passive verification (live). Result: 1 confirmed vulnerability (CTM-F-001, Medium), 5 hardening recommendations (H-1 to H-5), 1 item for a team policy decision (`/docs` exposure). Cross-session isolation, CORS, stored-XSS resistance and error handling all passed.

### SEC 2.1 - Remediate CTM-F-001 and retest
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** verify the BE 2.4 fix, then re-run pen-test CTM-PT-005b locally and repeat the check on the live deployment.
- **Why:** closes the only confirmed vulnerability.
- **Blocks / Blocked by:** pair with BE 2.4.

### SEC 2.2 - Security headers (H-3)
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** add `Content-Security-Policy`, `X-Frame-Options` (or CSP `frame-ancestors`) and `X-Content-Type-Options` on frontend and backend responses. Confirmed still missing on the live site.
- **Why:** overdue hardening, now confirmed live.
- **Blocks / Blocked by:** coordinate with FE 2.4.

### SEC 2.3 - Rate limiting (H-4)
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** add rate limiting, including on anonymous session creation (currently unbounded).
- **Why:** pen-test H-4 / team risk R05.
- **Blocks / Blocked by:** with backend.

### SEC 2.4 - /docs and /openapi.json exposure decision
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** team decides whether the API schema stays public on the live backend; record the decision here.
- **Why:** flagged in the pen test as a policy call, not an automatic finding.
- **Blocks / Blocked by:** needs a team decision.

### SEC 2.5 - Sign-on design (token now, TOTP later)
- **Status:** [WIP]  **Owner:** TBD  **Date:** TBD
- **What:** spec the token-generation sign-on for this iteration. Also research a TOTP authenticator method for Iteration 3 as suggested by the tutor. Note: TOTP (RFC 6238, time-based one-time passwords, e.g. Google Authenticator) is not yet understood by the team - the action is to research a Python approach (for example the `pyotp` library and a QR provisioning URI) and write it up before committing to it. TOTP is a possibility for this iteration only if time allows; the plan is token this iteration, TOTP in Iteration 3.
- **Why:** goal 3.
- **Blocks / Blocked by:** B3. Blocks FE 2.3, BE 2.3.

### SEC 2.6 - Threat-model the new surfaces
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** extend the threat model to cover the LLM (prompt injection, PII leakage, unsafe output) and the new auth flow (risk R11 was reserved for this).
- **Why:** new features add new attack surface.
- **Blocks / Blocked by:** after the AI and auth designs exist.

---

## AI (AI)

New for Iteration 2. Goal: an LLM we are training that turns a user's captured profile (role, years, skills, break, direction) into personalised workplace scenario questions.

### AI 2.1 - Define the scenario contract
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** agree the exact request (which profile fields the model receives) and response (the JSON shape of a scenario: id, prompt/question, options or expected-answer form, scoring) that the backend will consume.
- **Why:** everything downstream (backend endpoints, frontend screen, progress storage) depends on this shape.
- **Blocks / Blocked by:** blocks B1, BE 2.1, FE 2.1, DB 2.2.

### AI 2.2 - Model and training
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** decide the model/provider, gather/prepare training data, design prompts, and produce structured, validated output.
- **Why:** the engine behind Workplace Scenarios.
- **Blocks / Blocked by:** none to start; feeds AI 2.1.

### AI 2.3 - Serving and guardrails
- **Status:** [TODO]  **Owner:** TBD  **Date:** TBD
- **What:** expose the model to the backend behind an agreed interface; add guardrails (no leaking of personal data, safe/appropriate content, predictable output the backend can parse).
- **Why:** safe, reliable integration.
- **Blocks / Blocked by:** coordinate with SEC 2.6 and BE 2.1.
