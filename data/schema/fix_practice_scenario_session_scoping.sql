-- scenario_id alone was the primary key, but it's a deterministic value shared
-- by every session practicing the same role+difficulty, causing sessions to
-- silently collide and overwrite each other. This rescopes both tables' keys
-- to (session_id, scenario_id) so each session gets its own row.

DO $$
DECLARE
    pk_name text;
BEGIN
    SELECT conname INTO pk_name
    FROM pg_constraint
    WHERE conrelid = 'practice_scenario'::regclass AND contype = 'p';

    EXECUTE format('ALTER TABLE practice_scenario DROP CONSTRAINT %I', pk_name);
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
    pk_name text;
    fk_name text;
BEGIN
    SELECT conname INTO pk_name
    FROM pg_constraint
    WHERE conrelid = 'practice_scenario_option'::regclass AND contype = 'p';

    SELECT conname INTO fk_name
    FROM pg_constraint
    WHERE conrelid = 'practice_scenario_option'::regclass AND contype = 'f';

    EXECUTE format('ALTER TABLE practice_scenario_option DROP CONSTRAINT %I', pk_name);
    EXECUTE format('ALTER TABLE practice_scenario_option DROP CONSTRAINT %I', fk_name);
    EXECUTE 'ALTER TABLE practice_scenario_option ALTER COLUMN session_id SET NOT NULL';
    EXECUTE 'ALTER TABLE practice_scenario_option ADD PRIMARY KEY (session_id, scenario_id, option_id)';
    EXECUTE '
        ALTER TABLE practice_scenario_option
        ADD CONSTRAINT practice_scenario_option_scenario_fkey
        FOREIGN KEY (session_id, scenario_id)
        REFERENCES practice_scenario(session_id, scenario_id)
        ON DELETE CASCADE';
END $$;
