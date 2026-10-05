-- Iteration 3, BE 3.2: job descriptions a user pastes and their extracted
-- requirements (AI Task 1 / AI 3.1). One row per paste, not one per user -
-- see CTM_Iteration3_Endpoints_AI_Database_Spec.docx Section 9.1.

CREATE TABLE job_description (
    job_description_id         VARCHAR(64) PRIMARY KEY,
    owner_token_hash           VARCHAR(64) NOT NULL REFERENCES anon_session(token_hash) ON DELETE CASCADE,
    raw_text                   TEXT NOT NULL,
    extracted_skills           JSONB NOT NULL DEFAULT '[]',
    extracted_responsibilities TEXT[] NOT NULL DEFAULT '{}',
    min_years_experience       INT,
    keywords                   TEXT[] NOT NULL DEFAULT '{}',
    role_title_guess           TEXT,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_job_description_owner ON job_description(owner_token_hash);
