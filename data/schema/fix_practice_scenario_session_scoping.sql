-- scenario_id alone was the primary key, but it's a deterministic value shared
-- by every session practicing the same role+difficulty, causing sessions to
-- silently collide and overwrite each other. This rescopes both tables' keys
-- to (session_id, scenario_id) so each session gets its own row.

DO $$
DECLARE
    option_fk_name text;
    scenario_pk_name text;
BEGIN
    -- Must drop the option table's FK first - it depends on the index
    -- backing practice_scenario's current primary key.
    SELECT conname INTO option_fk_name
    FROM pg_constraint
    WHERE conrelid = 'practice_scenario_option'::regclass AND contype = 'f';
    EXECUTE format('ALTER TABLE practice_scenario_option DROP CONSTRAINT %I', option_fk_name);

    SELECT conname INTO scenario_pk_name
    FROM pg_constraint
    WHERE conrelid = 'practice_scenario'::regclass AND contype = 'p';
    EXECUTE format('ALTER TABLE practice_scenario DROP CONSTRAINT %I', scenario_pk_name);
    EXECUTE 'ALTER TABLE practice_scenario ADD PRIMARY KEY (session_id, scenario_id)';
END $$;

ALTER TABLE practice_scenario_option
    ADD COLUMN IF NOT EXISTS session_id VARCHAR(64);

UPDATE practice_scenario_option po
SET session_id = ps.session_id
FROM practice_scenario ps
WHERE po.scenario_id = ps.scenario_id
  AND po.session_id IS NULL;

-- Orphaned rows the backfill above couldn't match (session already lost to the collision).
DELETE FROM practice_scenario_option WHERE session_id IS NULL;

DO $$
DECLARE
    option_pk_name text;
BEGIN
    SELECT conname INTO option_pk_name
    FROM pg_constraint
    WHERE conrelid = 'practice_scenario_option'::regclass AND contype = 'p';

    EXECUTE format('ALTER TABLE practice_scenario_option DROP CONSTRAINT %I', option_pk_name);
    EXECUTE 'ALTER TABLE practice_scenario_option ALTER COLUMN session_id SET NOT NULL';
    EXECUTE 'ALTER TABLE practice_scenario_option ADD PRIMARY KEY (session_id, scenario_id, option_id)';
    EXECUTE '
        ALTER TABLE practice_scenario_option
        ADD CONSTRAINT practice_scenario_option_scenario_fkey
        FOREIGN KEY (session_id, scenario_id)
        REFERENCES practice_scenario(session_id, scenario_id)
        ON DELETE CASCADE';
END $$;
