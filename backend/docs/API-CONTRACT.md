# CareerTimeMachine Iteration 1 API Contract

Base URL: `/api/v1`

Protected endpoints require the anonymous session token in the request header:

```js
const headers = {
  "Content-Type": "application/json",
  "X-Session-Token": sessionToken,
};
```

All error responses use this shape:

```json
{
  "error": {
    "code": "HTTP_400",
    "message": "Human readable message",
    "details": []
  }
}
```

## Health

### `GET /health`

Checks whether the API is running.

Request body: none

Success `200`:

```json
{
  "status": "ok"
}
```

Frontend example:

```js
const res = await fetch("/api/v1/health");
```

## Anonymous Sessions

### `POST /anonymous-sessions`

Starts an anonymous journey and generates its access token (AC 3.1.2). Show the
returned token to the user, store it in the frontend and send it as
`X-Session-Token` on later protected requests.

The token is a 43-character URL-safe random string. **This is the only
response that ever contains it.** The backend stores only its SHA-256 hash, so
a lost token cannot be recovered or re-displayed by the API.

Request body: none

Success `201`:

```json
{
  "token": "generated-token",
  "created_at": "2026-08-29T01:00:00Z",
  "last_seen_at": "2026-08-29T01:00:00Z"
}
```

Frontend example:

```js
const res = await fetch("/api/v1/anonymous-sessions", { method: "POST" });
const session = await res.json();
```

### `GET /anonymous-sessions/current`

Validates an existing access token (AC 3.1.3). `200` means the token is
recognised; the frontend can then set it as the active token and load the
saved journey with `GET /profile` / `GET /career-journey`. Each successful
check updates `last_seen_at`.

**Changed in Iteration 2:** the response no longer echoes the token.

Request body: none

Success `200`:

```json
{
  "created_at": "2026-08-29T01:00:00Z",
  "last_seen_at": "2026-09-14T09:30:00Z"
}
```

Errors:

- `401` `"Missing session token"` when the header is absent.
- `401` `"Invalid session token"` when the token is unknown, empty, longer
  than 128 characters or contains characters outside `A-Z a-z 0-9 - _`.
  Unknown and malformed tokens get the identical response.

Frontend example:

```js
const res = await fetch("/api/v1/anonymous-sessions/current", { headers });
```

## Catalogue

Each catalogue endpoint returns a list of stable IDs and display labels.

### `GET /catalogue/roles`

### `GET /catalogue/experience-options`

### `GET /catalogue/skills`

Accepts an optional `role_id` query parameter. When present, returns only
the skills linked to that role (via the real `role_skill` table), sorted
`in_demand` desc, then `hot_technology` desc, then label. Without it, returns
the full skill catalogue unsorted-by-relevance. Each item additionally
carries `in_demand` and `hot_technology` booleans (default `false` for every
other catalogue kind).

```js
const res = await fetch(`/api/v1/catalogue/skills?role_id=${roleId}`);
```

### `GET /catalogue/responsibilities`

### `GET /catalogue/break-reasons`

### `GET /catalogue/return-statuses`

### `GET /catalogue/career-areas`

Request body: none

Success `200`:

```json
[
  {
    "id": "software_engineer",
    "label": "Software Engineer",
    "in_demand": false,
    "hot_technology": false
  }
]
```

Frontend example:

```js
const res = await fetch("/api/v1/catalogue/skills");
const skills = await res.json();
```

## Profile

Profile data belongs to the anonymous session. There is no profile ID in the URL.

### `GET /profile`

Returns the current session's profile, creating an empty draft if none exists.

Request body: none

Success `200`:

```json
{
  "role_id": null,
  "role_other_text": null,
  "years_experience": null,
  "skill_ids": [],
  "custom_skills": [],
  "responsibility_ids": [],
  "custom_responsibilities": [],
  "break_reason": null,
  "break_reason_other_text": null,
  "break_started_on": null,
  "planned_return_date": null,
  "return_date_unsure": false,
  "break_duration_months": null,
  "return_readiness": null,
  "area_to_explore": null,
  "confirmed": false
}
```

Errors:

- `401` when `X-Session-Token` is missing or invalid.

Frontend example:

```js
const res = await fetch("/api/v1/profile", { headers });
```

### `PATCH /profile`

Progressively updates profile fields. Any successful profile edit resets
`confirmed` to `false`.

Request body: any subset of:

```json
{
  "role_id": "software_engineer",
  "role_other_text": null,
  "years_experience": "5",
  "skill_ids": ["python", "rest_apis"],
  "custom_skills": ["Mentoring"],
  "responsibility_ids": ["api_design"],
  "custom_responsibilities": ["Release planning"],
  "break_reason": "prefer_not_to_say",
  "break_reason_other_text": null,
  "break_started_on": "2024-01-01",
  "planned_return_date": "2024-07-01",
  "return_date_unsure": false
}
```

Success `200`: same shape as `GET /profile`

Errors:

- `400` for invalid catalogue IDs or invalid date rule.
- `401` when `X-Session-Token` is missing or invalid.
- `422` for invalid request types, such as a malformed date.

Frontend example:

```js
const res = await fetch("/api/v1/profile", {
  method: "PATCH",
  headers,
  body: JSON.stringify({ years_experience: "5" }),
});
```

### `POST /profile/confirm`

Confirms the profile after completeness validation.

Request body: none

Success `200`: same shape as `GET /profile`, with `"confirmed": true`

Errors:

- `400` with code `PROFILE_INCOMPLETE` when required fields are missing.
- `401` when `X-Session-Token` is missing or invalid.

Frontend example:

```js
const res = await fetch("/api/v1/profile/confirm", {
  method: "POST",
  headers,
});
```

### `DELETE /profile`

Deletes the profile for the current anonymous session.

Request body: none

Success `204`: empty body

Errors:

- `401` when `X-Session-Token` is missing or invalid.

Frontend example:

```js
const res = await fetch("/api/v1/profile", {
  method: "DELETE",
  headers,
});
```

## Career Journey

### `GET /career-journey`

Returns a structured chronological summary built from the confirmed profile.
This endpoint returns JSON only; it does not return HTML or styling.

Request body: none

Success `200`:

```json
{
  "previous_role": {
    "id": "software_engineer",
    "label": "Software Engineer"
  },
  "years_experience": {
    "id": "10_plus",
    "label": "10+ years"
  },
  "career_break": {
    "break_started_on": "2023-01-01",
    "planned_return_date": "2024-01-01",
    "return_date_unsure": false,
    "break_duration_months": 12
  },
  "current_return_status": {
    "id": "preparing",
    "label": "I'm preparing to return"
  },
  "selected_skills": {
    "catalogue_skills": [
      {
        "id": "python",
        "label": "Python"
      }
    ],
    "custom_skills": ["Mentoring"]
  },
  "strengths": []
}
```

Errors:

- `401` when `X-Session-Token` is missing or invalid.
- `409` when the profile is not confirmed.

Frontend example:

```js
const res = await fetch("/api/v1/career-journey", { headers });
```

## Career Translation

### `GET /career-translation`

**Changed from the original Iteration 1 shape** — this no longer maps skills
to career areas (that model needed `skill_area_mapping`/`career_area`, which
are still unseeded — see the data handover). It now implements AC 2.2.1
directly: compares the user's recorded skills against the current in-demand
skills for her selected role, using the real `role_skill` table.

- `owned_skills` — every catalogue skill_id on the profile, each flagged
  `still_relevant` if it's `in_demand` for the user's role.
- `custom_skills` — passed through as plain strings; there's no relevance
  concept for free text.
- `new_horizons` — in-demand skills for the role that the user hasn't
  recorded ("New Horizons" in the AC).
- `role_data_available` — `false` when no role is selected yet, or the role
  has no skill data at all. The frontend shows *"Current skill demand
  information is unavailable for this role."* in that case (AC 2.2.1's
  required exception copy).
- When `role_data_available` is `true` but `new_horizons` is empty, the
  frontend shows *"You're already aligned with the current skill demand for
  your selected role."* (also AC-required copy).

Request body: none

Success `200`:

```json
{
  "role_label": "Web Developer",
  "role_data_available": true,
  "owned_skills": [
    { "id": "react", "label": "React", "still_relevant": true }
  ],
  "custom_skills": ["Rust"],
  "new_horizons": [
    { "id": "git", "label": "Git" }
  ]
}
```

No role selected yet:

```json
{
  "role_label": null,
  "role_data_available": false,
  "owned_skills": [],
  "custom_skills": [],
  "new_horizons": []
}
```

Errors:

- `401` when `X-Session-Token` is missing or invalid.

Frontend example:

```js
const res = await fetch("/api/v1/career-translation", { headers });
```

**Removed:** `GET /career-translation/{skill_id}` no longer exists — the new
shape is a single aggregate view, not a per-skill lookup.

## Career Direction

### `GET /career-direction`

Returns the current direction selections stored on the profile.

Request body: none

Success `200`:

```json
{
  "return_readiness": "preparing",
  "area_to_explore": "cloud_native_engineering"
}
```

Errors:

- `401` when `X-Session-Token` is missing or invalid.

Frontend example:

```js
const res = await fetch("/api/v1/career-direction", { headers });
```

### `PATCH /career-direction`

Saves either or both career-direction fields. Sending `null` clears a field.
This endpoint records the choice only; it does not generate scenarios.

Request body:

```json
{
  "return_readiness": "preparing",
  "area_to_explore": "cloud_native_engineering"
}
```

Success `200`: same shape as `GET /career-direction`

Errors:

- `400` for invalid `return-statuses` or `career-areas` catalogue IDs.
- `401` when `X-Session-Token` is missing or invalid.
- `422` for invalid request body types.

Frontend example:

```js
const res = await fetch("/api/v1/career-direction", {
  method: "PATCH",
  headers,
  body: JSON.stringify({ area_to_explore: "cloud_native_engineering" }),
});
```

## Practice Role (Iteration 2)

The role chosen on Your Direction for workplace practice (AC 4.1.2). It is
stored against the token, so it is available after a refresh and to
`POST /practice-sessions` without the user re-entering anything.

### `GET /practice-role`

Request body: none

Success `200`:

```json
{
  "role_id": "software_engineer",
  "role_label": "Software Engineer",
  "source": "previous"
}
```

All three fields are `null` when no role is selected. A `previous` selection
also reads as `null` once the saved previous role (`PATCH /profile` `role_id`)
has been changed, so the user chooses again.

Errors:

- `401` when `X-Session-Token` is missing or invalid.

### `PUT /practice-role`

Request body (both fields required, no other fields allowed):

```json
{
  "role_id": "web_developer",
  "source": "predicted"
}
```

- `role_id`: role catalogue id, 1-64 characters of `a-z 0-9 _`.
- `source`: `"previous"` or `"predicted"`.

Success `200`: same shape as `GET /practice-role`. For the `other` previous
role, `role_label` is the user's `role_other_text`.

Errors:

- `400` `"Invalid role_id: <id>"` when the id is not in the role catalogue
  (or is `other` with `source: "predicted"`).
- `400` `"role_id must match the saved previous role"` when `source` is
  `previous` but the id is not the profile's `role_id`.
- `401` when `X-Session-Token` is missing or invalid.
- `422` `REQUEST_VALIDATION_ERROR` for a missing field, bad `source`, bad id
  format or an unexpected field.

A rejected request leaves the existing selection unchanged.

Frontend example:

```js
const res = await fetch("/api/v1/practice-role", {
  method: "PUT",
  headers,
  body: JSON.stringify({ role_id: "software_engineer", source: "previous" }),
});
```

## Workplace Practice Sessions (Iteration 2)

A practice session is started from the saved practice role and saved career
information, so nothing is re-entered (AC 4.1.3, 4.2.2). Each session belongs
to the token that started it. Another token's session always looks exactly
like one that does not exist (`404`).

> **Development provider:** scenarios currently come from a curated,
> hand-written provider (`app/providers/curated_scenario_provider.py`), not the
> production AI integration. The response shape below is the contract the AI
> provider must satisfy (`app/providers/scenario_provider.py`).

Session object (returned by every endpoint in this section):

```json
{
  "session_id": "3f5b2c1e9a7d4e0f8b6a2c4d1e3f5a7b",
  "role": { "id": "software_engineer", "label": "Software Engineer", "source": "previous" },
  "duration": "standard",
  "duration_minutes": 10,
  "difficulty": "guided",
  "status": "active",
  "created_at": "2026-09-14T10:00:00Z",
  "updated_at": "2026-09-14T10:00:00Z",
  "completed_at": null,
  "scenarios": [
    {
      "scenario_id": "software_slow_release",
      "title": "Slow responses after a release",
      "workplace_area": "Engineering team desk",
      "situation": "Your team shipped an update ...",
      "task": "Write a short message to your lead ...",
      "activity_type": "written_response",
      "guidance": ["Think about what changed in this morning's release."],
      "skills_used": ["Debugging", "Communication", "API design", "Python"],
      "new_skill_focus": "Observability",
      "status": "current",
      "response": null,
      "feedback": null,
      "feedback_status": null
    }
  ],
  "progress": {
    "status": "active",
    "total_activities": 1,
    "completed_activities": 0,
    "current_scenario_id": "software_slow_release"
  }
}
```

- `status`: `active`, `completed` or `abandoned` (replaced by a newer session).
- `guidance`: every hint for `guided`, one for `standard`, none for `challenge`.

### `POST /practice-sessions`

Request body (both required, no other fields):

```json
{ "duration": "standard", "difficulty": "guided" }
```

- `duration`: `quick` (5 min), `standard` (10 min), `challenge` (15 min).
- `difficulty`: `guided`, `standard`, `challenge`.

Starting a session while another is active marks the older one `abandoned`.

Success `201`: session object.

Errors:

- `401` missing/invalid token.
- `409` `PROFILE_NOT_CONFIRMED` - no confirmed profile yet.
- `409` `PRACTICE_ROLE_REQUIRED` - no practice role saved (AC 4.1.2 "Please select a role to continue").
- `422` `REQUEST_VALIDATION_ERROR` - missing or unsupported duration/difficulty
  (AC 4.2.2 "Choose a practice time and difficulty to continue").
- `503` `SCENARIO_UNAVAILABLE` - the provider failed, timed out or returned
  invalid content. No session is created (AC 4.1.3 "We couldn't start your
  workplace practice").

### `GET /practice-sessions/current`

Returns the active session so the user can resume (AC 4.3.4).

Errors: `401`; `404` `PRACTICE_SESSION_NOT_FOUND` when there is no active session.

### `GET /practice-sessions/{session_id}`

Errors: `401`; `404` `PRACTICE_SESSION_NOT_FOUND`; `422` for an id longer than 64 characters.

### `POST /practice-sessions/{session_id}/complete`

Marks the session `completed` and sets `completed_at` (AC 4.5.3). Calling it
again on a completed session returns the same result.

Errors: `401`; `404` `PRACTICE_SESSION_NOT_FOUND`; `409`
`PRACTICE_SESSION_NOT_ACTIVE` for an abandoned session.

## Scenario Responses, Feedback and Progress (Iteration 2)

### `POST /practice-sessions/{session_id}/scenarios/{scenario_id}/response`

Saves the user's written response to a scenario in her **active** session and
returns reflective feedback (AC 4.4.2, 4.5.1, 4.5.2). The response is stored as
text only; the backend never executes submitted content.

Request body (no other fields allowed):

```json
{ "response_text": "I would first check what changed in this morning's release..." }
```

- `response_text`: 1-5000 characters after trimming outer whitespace.

Success `201`:

```json
{
  "session_id": "3f5b2c1e9a7d4e0f8b6a2c4d1e3f5a7b",
  "scenario": {
    "scenario_id": "software_slow_release",
    "status": "completed",
    "response": {
      "response_text": "I would first check what changed ...",
      "submitted_at": "2026-09-14T10:06:00Z"
    },
    "feedback_status": "available",
    "feedback": {
      "what_worked_well": ["You set out your own approach to the situation, ..."],
      "areas_to_consider": ["How would you confirm the release caused the slowdown ...?"],
      "skill_to_explore": {
        "skill": "Observability",
        "why_relevant": "Modern teams use logs, metrics and traces ..."
      }
    },
    "...": "other scenario fields as in the session object"
  },
  "progress": {
    "status": "active",
    "total_activities": 1,
    "completed_activities": 1,
    "current_scenario_id": null
  }
}
```

Feedback never contains a score, pass/fail result or employability judgement.
Provider feedback that includes extra fields or wording such as a score is
discarded. If feedback cannot be generated (provider failure, timeout or
invalid content), the response is **still saved**, `feedback` is `null` and
`feedback_status` is `"unavailable"` (AC 4.5.1 "We couldn't generate your
personalised feedback. You can continue to the next activity.").
`skill_to_explore` may be `null` when no skill is identified (AC 4.5.2).

Errors:

- `401` missing/invalid token.
- `404` `PRACTICE_SESSION_NOT_FOUND` - unknown session or another user's session.
- `404` `SCENARIO_NOT_FOUND` - the scenario is not part of this session.
- `409` `PRACTICE_SESSION_NOT_ACTIVE` - the session is completed or abandoned.
- `409` `RESPONSE_ALREADY_SUBMITTED` - a response already exists; the first one is kept.
- `422` `REQUEST_VALIDATION_ERROR` - empty, whitespace-only, over-length or extra fields.

### `GET /practice-sessions/{session_id}/progress`

Success `200`:

```json
{
  "status": "active",
  "total_activities": 1,
  "completed_activities": 1,
  "current_scenario_id": null
}
```

When `status` is `active` and `current_scenario_id` is `null`, every available
activity is done and the frontend can offer to complete the session (AC 4.5.3
"You've completed the available activities for this practice session.").
Each session currently contains one scenario; a "next activity" endpoint is not
implemented yet.

Errors: `401`; `404` `PRACTICE_SESSION_NOT_FOUND`.
