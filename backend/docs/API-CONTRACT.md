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

Starts an anonymous journey. Store the returned token in the frontend and send it
as `X-Session-Token` on later protected requests.

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

Returns the current anonymous session.

Request body: none

Success `200`: same shape as `POST /anonymous-sessions`

Errors:

- `401` when `X-Session-Token` is missing or invalid.

Frontend example:

```js
const res = await fetch("/api/v1/anonymous-sessions/current", { headers });
```

## Catalogue

Each catalogue endpoint returns a list of stable IDs and display labels.

### `GET /catalogue/roles`

### `GET /catalogue/experience-options`

### `GET /catalogue/skills`

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
    "label": "Software Engineer"
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

Returns deterministic career-area mappings for the user's selected catalogue
skills. Custom skills are not mapped.

Request body: none

Success `200`:

```json
[
  {
    "previous_skill": {
      "id": "rest_apis",
      "name": "REST APIs"
    },
    "connected_areas": [
      {
        "id": "cloud_native_engineering",
        "name": "Cloud-Native Engineering"
      }
    ]
  }
]
```

Errors:

- `401` when `X-Session-Token` is missing or invalid.

Frontend example:

```js
const res = await fetch("/api/v1/career-translation", { headers });
```

### `GET /career-translation/{skill_id}`

Returns deterministic career-area mappings for one selected catalogue skill.

Request body: none

Success `200`: one object from the `GET /career-translation` list

Errors:

- `401` when `X-Session-Token` is missing or invalid.
- `404` when the skill is not selected in the user's profile.

Frontend example:

```js
const res = await fetch("/api/v1/career-translation/rest_apis", { headers });
```

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
