-- Iteration 3, AC 4.4.6: a live (AI-generated) question arrives with the
-- reflective feedback for each of its options. Unlike the static pool there
-- is nowhere to look that feedback up again when she answers, so it is kept
-- with the scenario. NULL for every static scenario. Safe to run twice.

ALTER TABLE practice_scenario
    ADD COLUMN IF NOT EXISTS option_feedback JSONB;
