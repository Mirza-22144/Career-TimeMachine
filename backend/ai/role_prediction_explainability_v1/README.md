# Career Time Machine — Predictive Role Explainability V1

This package adds deterministic, evidence-gated explanations to the existing Version 2 two-role career recommender.

## Behaviour

For each existing recommendation, the feature returns:

- a plain-language summary;
- up to five verified matching skills;
- controlled explanation reason codes.

The explanation layer does not select or reorder the roles.

## Verification

- 27/27 production roles covered
- 81/81 profile-variant tests passed
- original role rankings preserved
- repeated responses deterministic
- matched-skill claims evidence-gated
- internal ranking scores hidden
- 4/4 input-security tests passed
- original model bundle unchanged
- no Gemini calls
- no model retraining

See `BACKEND_INTEGRATION.md` for the integration instructions.
