
-- create table role for the previous roles the user can pick
CREATE TABLE role (
    id     VARCHAR(64) PRIMARY KEY, -- has a unique id and serves as a primary key
    label  TEXT NOT NULL -- human readable name as shown in UI
);



-- previous experience 
CREATE TABLE experience_option (
    id     VARCHAR(64) PRIMARY KEY, -- can be a number or something like 5 plus
    label  TEXT NOT NULL
);

-- responsibilities a user can select
CREATE TABLE responsibility (
    id     VARCHAR(64) PRIMARY KEY,
    label  TEXT NOT NULL
);

-- table for break reason options
CREATE TABLE break_reason (
    id     VARCHAR(64) PRIMARY KEY,
    label  TEXT NOT NULL
);

CREATE TABLE return_status (
    id     VARCHAR(64) PRIMARY KEY,
    label  TEXT NOT NULL        -- displays text such ready to return or not
);


-- skill table from O*NET DATA
CREATE TABLE skill (
    id              VARCHAR(64) PRIMARY KEY,
    label           TEXT NOT NULL,   --
    category        TEXT,            -- groups the skill into a category and is optional
    hot_technology  BOOLEAN DEFAULT FALSE,  -- from O*NET Hot Technology flag
    in_demand       BOOLEAN DEFAULT FALSE,  -- is a flag which tells if the skill is in demand or not
    source          TEXT             -- displays the source as well for the user to verify
);


CREATE TABLE career_area (
    id               VARCHAR(64) PRIMARY KEY,
    label            TEXT NOT NULL,
    growth_outlook   TEXT,           -- tells the growth signal from O*NET Bright Outlook
    evidence_source  TEXT,           -- 'O*NET Bright Outlook 2024-2034'
    source_date      DATE            -- when the evidence is dated
);


-- USER DATA TABLES--

-- when the user uses the website and enters the details


-- one row per anonymous user
CREATE TABLE anon_session (
    token_hash    VARCHAR(64) PRIMARY KEY,   -- hashed token and never the raw token
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now() -- app updates this on each visit
);

-- professional background of the user--
CREATE TABLE profile (
    session_token_hash       VARCHAR(64) PRIMARY KEY
                                 REFERENCES anon_session(token_hash) ON DELETE CASCADE,
    role_id                  VARCHAR(64) REFERENCES role(id),                -- if user wants to delete , it deletes the profile
    role_other_text          TEXT,
    years_experience         VARCHAR(64) REFERENCES experience_option(id),   -- optional
    custom_skills            TEXT[] DEFAULT '{}',
    custom_responsibilities  TEXT[] DEFAULT '{}',  -- we use TEXT[] as the user can enter custom responsibilities in an array
    break_reason             VARCHAR(64) REFERENCES break_reason(id),      -- optional
    break_reason_other_text  TEXT,
    break_started_on         DATE,
    planned_return_date      DATE,  -- null if unsure
    return_date_unsure       BOOLEAN DEFAULT FALSE,
    break_duration_months    INT,
    return_readiness         VARCHAR(64) REFERENCES return_status(id),    -- optional
    area_to_explore          VARCHAR(64) REFERENCES career_area(id),      -- optional
    confirmed                BOOLEAN NOT NULL DEFAULT FALSE
);


-- JUNCTION TABLES --


CREATE TABLE profile_skill (
    session_token_hash  VARCHAR(64) NOT NULL  -- FK TO THE PROFILE
                            REFERENCES profile(session_token_hash) ON DELETE CASCADE,
    skill_id            VARCHAR(64) NOT NULL REFERENCES skill(id),  -- FK to skill
    PRIMARY KEY (session_token_hash, skill_id)  -- composite primary key means each skill appears once per profile
);

CREATE TABLE profile_responsibility (
    session_token_hash  VARCHAR(64) NOT NULL    -- FK to the profile
                            REFERENCES profile(session_token_hash) ON DELETE CASCADE,
    responsibility_id   VARCHAR(64) NOT NULL REFERENCES responsibility(id),
    PRIMARY KEY (session_token_hash, responsibility_id)  -- composite PK
);

CREATE TABLE skill_area_mapping (
    skill_id     VARCHAR(64) NOT NULL REFERENCES skill(id),
    area_id      VARCHAR(64) NOT NULL REFERENCES career_area(id),
    source       TEXT,          -- provenance for this specific connection
    source_date  DATE,
    notes        TEXT,          -- limitations / how the mapping was derived
    PRIMARY KEY (skill_id, area_id)
);



CREATE INDEX idx_skill_area_mapping_area ON skill_area_mapping(area_id);
CREATE INDEX idx_profile_skill_skill ON profile_skill(skill_id);
CREATE INDEX idx_profile_resp_resp ON profile_responsibility(responsibility_id);
