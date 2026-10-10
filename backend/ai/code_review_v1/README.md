# Iteration 3 Static Code-Review AI Handover

This package contains 324 validated, pre-generated code-review
activities covering 27 IT roles and three difficulty levels.

## Delivery mode

This handover is static-only. It does not perform live generation,
does not require a Gemini API key and never executes a code snippet.

The backend selects one activity matching the requested `role_id`
and `difficulty`.

## Dataset coverage

- 27 roles
- 3 difficulty levels
- 4 activities per role-difficulty combination
- 324 activities in total
- Exactly one backend-only correct option per activity
- Constructive feedback for all four options

## Privacy boundary

The frontend activity must not contain `correct_option_id` or the
complete `option_feedback` mapping. The backend retains those fields
and returns only the selected option's constructive feedback after
submission.

## Main file

`data/code_review_activity_pool_v1_final.json`

## Quality result

All 324 activities passed schema validation, independent Gemini
review or targeted revision, and the final deterministic audit.
The final audit found zero critical issues, zero structural warnings,
zero exact duplicate groups and zero near-duplicate pairs at the
configured threshold.
