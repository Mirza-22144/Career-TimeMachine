# Iteration 3 Drag-and-Drop AI

This handover contains the AI assets for the Iteration 3
drag-and-drop workplace communication activity.

## Static activities

The final static pool contains 324 validated activities:

- 27 roles
- 3 difficulty levels
- 4 activities per role and difficulty combination
- 3 blanks per activity
- 5 options per activity
- 3 intended placements
- 2 constructive distractors

## Live custom-skill generation

When a relevant custom skill is supplied, the live service uses:

- role ID
- custom skills
- years of experience
- responsibilities
- difficulty

The live generator uses gemini-3.5-flash-lite. It makes a maximum
of two generation attempts. If generation or validation fails,
the backend serves a matching validated static activity.

## Quality assurance

Static content was generated with gemini-3.5-flash and reviewed
with the separate gemini-3.8-flash model. The final static pool
passed deterministic schema and duplicate checks.

The corrected balanced live evaluation passed 6/6 tests.
The input-security suite passed 6/6 tests, and the forced static
fallback passed.

The original 4/6 live result is retained alongside the corrected
6/6 result as change-management evidence.

## Frontend security

The backend must retain fits_blank_id for evaluation but remove it
from the options returned to the frontend. The user must not
receive the intended answer mapping before submission.

## Secrets

No Gemini API key is included in this handover. The backend must
read the key from the GEMINI_API_KEY deployment environment
variable.

## Standalone backend entry point

Use `live_drag_and_drop_service.py`.

The main service class is:

`LiveDragAndDropService`

Initialise it with the final static-pool path and either:

- the `GEMINI_API_KEY` environment variable, or
- an authenticated Google Gen AI client supplied by the backend.

Call `generate()` with the validated request.

The returned object contains:

- `backend_activity`, which retains `fits_blank_id`;
- `frontend_activity`, which removes every `fits_blank_id`;
- `source`, which is either `live_gemini` or `static_fallback`;
- `attempts`, containing generation and validation evidence.

The production service makes no more than two live attempts before
serving a deterministic matching static fallback.
