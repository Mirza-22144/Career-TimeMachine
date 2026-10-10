# Model and Service Deployment

## Required environment variable

Set the Gemini API key as a backend secret:

GEMINI_API_KEY=<deployment secret>

Never commit the API key to Git or include it in frontend code.

## Models

Offline static generation:
- gemini-3.5-flash

Independent offline quality review:
- gemini-3.8-flash

Live custom-skill generation:
- gemini-3.5-flash-lite

The static-generation and review models are not required for
normal production requests. Production requires only the live
model and the validated static fallback pool.

## Runtime flow

1. Validate and sanitise the request.
2. Generate a live activity when a relevant custom skill exists.
3. Validate the exact response schema.
4. Apply the professional-plausibility gate.
5. Retry once if validation fails.
6. Serve a matching static fallback if both attempts fail.
7. Remove fits_blank_id before sending options to the frontend.
8. Retain the mapping on the backend for answer evaluation.
