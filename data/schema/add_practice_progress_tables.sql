-- Practice progress storage (Cross-team blocker B2) - see
-- Practice_Progress_DB_Additions.docx for the full rationale/ERD notes.
-- Matches this schema's existing conventions: flat columns, TEXT[] only
-- where custom_skills/custom_responsibilities already set the precedent,
-- and a junction table (not JSON) for the one real one-to-many relationship.

ALTER TABLE profile
    ADD COLUMN practice_role_id VARCHAR(64) REFERENCES role(id),
    ADD COLUMN practice_role_source VARCHAR(16);

CREATE TABLE practice_session (
    session_id       VARCHAR(64) PRIMARY KEY,
    owner_token_hash VARCHAR(64) NOT NULL REFERENCES anon_session(token_hash) ON DELETE CASCADE,
    role_id          VARCHAR(64) NOT NULL REFERENCES role(id),
    role_label       TEXT NOT NULL,
    role_source      VARCHAR(16) NOT NULL,
    duration         VARCHAR(16) NOT NULL,
    difficulty       VARCHAR(16) NOT NULL,
    status           VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at     TIMESTAMPTZ
);

CREATE INDEX idx_practice_session_owner ON practice_session(owner_token_hash);

CREATE TABLE practice_scenario (
    scenario_id       VARCHAR(64) PRIMARY KEY,
    session_id        VARCHAR(64) NOT NULL REFERENCES practice_session(session_id) ON DELETE CASCADE,
    title             TEXT NOT NULL,
    workplace_area    TEXT NOT NULL,
    situation         TEXT NOT NULL,
    task              TEXT NOT NULL,
    activity_type     VARCHAR(32) NOT NULL,
    guidance          TEXT[] NOT NULL DEFAULT '{}',
    skills_used       TEXT[] NOT NULL DEFAULT '{}',
    new_skill_focus   TEXT,
    status            VARCHAR(16) NOT NULL DEFAULT 'current',

    response_selected_option_id VARCHAR(64),
    response_text                TEXT,
    response_submitted_at        TIMESTAMPTZ,

    feedback_what_worked_well    TEXT[],
    feedback_areas_to_consider   TEXT[],
    feedback_trade_offs          TEXT[] NOT NULL DEFAULT '{}',
    feedback_skill_to_explore_title TEXT,
    feedback_skill_to_explore_why   TEXT,
    feedback_status              VARCHAR(16)
);

CREATE INDEX idx_practice_scenario_session ON practice_scenario(session_id);

CREATE TABLE practice_scenario_option (
    scenario_id  VARCHAR(64) NOT NULL REFERENCES practice_scenario(scenario_id) ON DELETE CASCADE,
    option_id    VARCHAR(64) NOT NULL,
    text         TEXT NOT NULL,
    PRIMARY KEY (scenario_id, option_id)
);
