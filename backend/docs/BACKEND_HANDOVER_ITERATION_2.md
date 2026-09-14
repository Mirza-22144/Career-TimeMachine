# Backend Handover - Iteration 2

| | |
|---|---|
| Date | 2026-09-14 |
| Branch | `iteration-2-backend` |
| Backend scope in this handover | Token backend and career-profile continuity (US 3.1, 3.2, 3.3), CTM-F-001 fix |
| Contract reference | `backend/docs/API-CONTRACT.md` |

This handover is written for the frontend integration of the access token. It
will be extended as the selected-role and workplace-practice backend lands.

## 1. What is ready

| Area | Status |
|---|---|
| Token generation (AC 3.1.2) | Ready - real backend token, replaces the frontend mock |
| Token validation (AC 3.1.3) | Ready - `GET /anonymous-sessions/current` |
| Save / edit / retrieve career info against one token (US 3.2, 3.3) | Ready - existing profile endpoints, verified with tests |
| Cross-token isolation | Ready - verified with tests |
| CTM-F-001 (rejected update partly saved) | Fixed - regression tests added |
| Saved profile survives a backend restart | **Blocked** - storage is still in-memory (see section 7) |

## 2. Endpoints implemented or verified

All paths are under `/api/v1`. Every protected endpoint needs:

```http
X-Session-Token: <access token>
Content-Type: application/json
```

| Method | Path | Purpose | Token |
|---|---|---|---|
| `POST` | `/anonymous-sessions` | Generate a new access token (new journey) | No |
| `GET` | `/anonymous-sessions/current` | Validate an existing token | Yes |
| `GET` | `/profile` | Load saved career information (creates an empty draft for a token with none) | Yes |
| `PATCH` | `/profile` | Save / edit career information (partial update) | Yes |
| `POST` | `/profile/confirm` | Confirm the saved information | Yes |
| `DELETE` | `/profile` | Delete the saved profile | Yes |
| `GET` | `/career-journey` | Structured journey for the returning-user page (409 until confirmed) | Yes |
| `GET` / `PATCH` | `/career-direction` | Your Direction selections | Yes |
| `GET` | `/career-translation` | Skill Relevance Map | Yes |

### Generate a token

```http
POST /api/v1/anonymous-sessions
```

`201`:

```json
{
  "token": "Q2x0Zk9yX2V4YW1wbGVfb25seV9ub3RfYV90b2tlbg",
  "created_at": "2026-09-14T09:00:00Z",
  "last_seen_at": "2026-09-14T09:00:00Z"
}
```

This is the **only** response that contains the token. The backend stores just
its SHA-256 hash, so it cannot show the token again - "My Token" must read it
from frontend storage.

### Validate an existing token

```http
GET /api/v1/anonymous-sessions/current
X-Session-Token: <token the user typed>
```

`200` (token recognised - note the token is not echoed):

```json
{
  "created_at": "2026-09-14T09:00:00Z",
  "last_seen_at": "2026-09-14T09:30:00Z"
}
```

`401` for an unknown, empty, over-128-character or otherwise malformed token
(one identical response for all of them):

```json
{ "error": { "code": "HTTP_401", "message": "Invalid session token", "details": [] } }
```

`401` with `"Missing session token"` when the header is absent.

### Save and edit career information

```http
PATCH /api/v1/profile
X-Session-Token: <token>

{ "role_id": "software_engineer", "years_experience": "5", "skill_ids": ["python"] }
```

`200` returns the full profile. Any successful edit sets `confirmed` to `false`;
call `POST /profile/confirm` again after an edit (the frontend already does).

Errors: `400` invalid catalogue ID or `planned_return_date` before
`break_started_on`; `422` wrong types (e.g. malformed date); `400`
`PROFILE_INCOMPLETE` from confirm with the missing field names in `details`.
**A rejected update now leaves the saved profile exactly as it was**, which
matches AC 3.2.3 "Your previous information is still available".

## 3. Replacing the frontend token mock

The frontend currently generates a `CTM-XXXX-XXXX` token in the browser and
maps it to the backend session token in `localStorage`
(`frontend/src/accessToken.js`, `hooks/useAccessTokenFlow.js`). With the real
backend the **access token and the session token are the same value**, so the
mapping layer is no longer needed.

Suggested changes (frontend owner to make - backend has not edited frontend code):

1. **Generate Token** (`handleGenerateToken`): call
   `api.createSession(true)` and show the returned `token` in the
   Generated Token modal. Drop `generateMockToken()` and `recordTokenSession()`.
2. **Enter existing token** (`AccessTokenModal`): replace
   `isKnownToken(trimmed)` with `GET /anonymous-sessions/current` using the
   entered token as `X-Session-Token`.
   - `200` → valid; set it as the active token.
   - `401` → "That token isn't recognised. Please check it and try again."
   - network error / `5xx` → "We couldn't verify your access. Please try again."
3. **Returning journey** (`handleValidToken`): `api.restoreSession(token)`, then
   `GET /profile`. `confirmed: true` → Career Journey ("Welcome back");
   `confirmed: false` → the journey was never finished, send the user to Your Story.
4. **Stop the silent 401 retry in `api.js`.** `request()` currently creates a
   brand-new session on any `401`. For a returning user that silently swaps
   in an empty journey (the issue FE 2.6 worked around). Surface the `401` to
   the caller instead, and show the token-required / not-recognised message.
5. **Storage:** keep one token key (today `ctm_session_token` in `api.js` and
   `ctm_active_token` in `accessToken.js`). `KNOWN_TOKENS_KEY` and
   `TOKEN_SESSION_MAP_KEY` can be removed; keeping a list of raw tokens in
   `localStorage` is no longer needed.
6. **Copy text:** the "Your token looks like CTM-XXXX-XXXX" hint no longer
   matches. Real tokens are 43 URL-safe characters (`A-Z a-z 0-9 - _`).

## 4. Token and profile behaviour

- Tokens come from `secrets.token_urlsafe(32)` (256 bits of randomness).
- Only `sha256(token)` is stored, matching `anon_session.token_hash` in
  `data/schema/careertimemachine_schema.sql`.
- Raw tokens are never logged, never put in URLs and never returned after
  creation.
- Unknown and malformed tokens are rejected with the same `401`, and malformed
  ones are rejected before any storage lookup.
- Each successful token check updates `last_seen_at`.
- One token owns exactly one profile; edits replace values on that profile and
  never create a second one.
- A token only ever reads or changes its own profile and direction data.
- Profile validation runs on a copy; only a fully valid update is saved.

## 5. Tests run

```bash
cd backend
venv/bin/python -m pytest -q
```

Result on 2026-09-14: **61 passed, 0 failed** (baseline before this work:
19 passed, 10 failed).

New or updated tests:

- `tests/conftest.py` - fixed test catalogue. The 10 baseline failures were
  caused by roles/skills being empty with no database `.env`; tests now run
  offline and deterministically.
- `tests/test_token_access_api.py` - token format, validation, malformed and
  unknown tokens, every protected endpoint rejecting missing/invalid tokens,
  returning-user restore, edit without duplication, cross-token isolation,
  hash-only storage, no token in logs.
- `tests/test_profile_update_state.py` - CTM-F-001 regression (date rule and
  catalogue rejection leave stored state unchanged; valid edits still work).
- `tests/test_anonymous_sessions_api.py`, `tests/test_memory_session_repository.py`
  - updated for the hash-keyed store and the non-echoing `/current` response.

## 6. Known limitations

- **In-memory storage.** Sessions and profiles are lost when the API restarts or a
  Cloud Run instance is recycled. A token that worked before a restart then
  gets `401`. The frontend should treat that as "token not recognised", not
  silently create a new session.
- **No token expiry.** AC 3.1 mentions expired tokens, but no expiry period has
  been agreed. Needs a team/security decision.
- **No rate limiting** on token creation or validation (tracked as SEC 2.3).
- Free-text profile length caps (BE 2.5 / pen-test H-1, H-2) are not part of
  this change.

## 7. Blockers and dependencies

| Blocker | Needs | Owner |
|---|---|---|
| Restart persistence for sessions and profiles (card Subtask 3) | Confirmed deployed `anon_session` / `profile` / `profile_skill` / `profile_responsibility` tables and connection details. The `profile` table's foreign keys reference `career_area`, `return_status`, `break_reason`, `experience_option` and `responsibility`, which are still unseeded, so writes would fail until DB 2.3 is done. | Database |
| Token expiry policy | Agreed expiry period (or "no expiry") | Team / Security |
| Real token in the UI | Section 3 changes | Frontend |

## 8. Files changed (Phase 1)

- `backend/app/core/tokens.py` (new)
- `backend/app/services/session_service.py`
- `backend/app/services/profile_service.py`
- `backend/app/repositories/interfaces/session_repository.py`
- `backend/app/repositories/interfaces/profile_repository.py`
- `backend/app/repositories/memory/memory_session_repository.py`
- `backend/app/repositories/memory/memory_profile_repository.py`
- `backend/app/schemas/anonymous_session.py`
- `backend/app/api/routes/anonymous_sessions.py`, `profile.py`, `career_direction.py`, `career_journey.py`, `career_translation.py`
- `backend/docs/API-CONTRACT.md`
- `backend/tests/conftest.py` (new), `test_token_access_api.py` (new), `test_profile_update_state.py` (new), `test_anonymous_sessions_api.py`, `test_memory_session_repository.py`

## 9. Next recommended integration step

Frontend: apply section 3 steps 1-4 against a local backend
(`uvicorn app.main:app --reload`), then run the generate → save → close tab →
re-enter token → Career Journey flow end to end. Database: confirm the user
data tables and seeded catalogue tables so the Postgres session/profile
repositories can be written against them.
