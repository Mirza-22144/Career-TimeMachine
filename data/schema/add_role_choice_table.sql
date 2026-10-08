-- Iteration 3, AC 3.4.1: every role a user has chosen to practise, with the
-- date she chose it, for the dashboard's "Your roadmaps" list. One row per
-- (user, role); choosing the same role again updates the date.
-- Safe to run more than once.

CREATE TABLE IF NOT EXISTS role_choice (
    owner_token_hash VARCHAR(64) NOT NULL REFERENCES anon_session(token_hash) ON DELETE CASCADE,
    role_id          VARCHAR(64) NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    chosen_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (owner_token_hash, role_id)
);
