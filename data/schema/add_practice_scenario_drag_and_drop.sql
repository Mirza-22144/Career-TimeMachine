-- Drag and Drop activities (Iteration 3, US 4.6).
--
-- content: the server-only part of a drag and drop activity - the message
-- template, which blank each phrase is meant for, and the feedback for
-- every phrase. It is never sent to the browser as it is.
-- response_placements: what she submitted - blank id -> phrase id.
--
-- Safe to run more than once.
ALTER TABLE practice_scenario
    ADD COLUMN IF NOT EXISTS content JSONB,
    ADD COLUMN IF NOT EXISTS response_placements JSONB;
