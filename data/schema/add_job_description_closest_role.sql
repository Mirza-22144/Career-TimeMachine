-- Iteration 3, AC 5.2.2: remember which role the user said is closest to
-- each job description, so reopening that job's roadmap does not ask again.
-- Run AFTER add_job_description_table.sql. Safe to run more than once.
--
-- ON DELETE SET NULL: if a role is ever removed from the catalogue, the job
-- description stays and simply forgets the choice.

ALTER TABLE job_description
    ADD COLUMN IF NOT EXISTS closest_role_id VARCHAR(64) REFERENCES role(id) ON DELETE SET NULL;
