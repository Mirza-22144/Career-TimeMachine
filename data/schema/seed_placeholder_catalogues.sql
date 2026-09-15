-- Seeds the catalogue tables that "profile" has foreign keys into, using
-- the exact same ids/labels already used by MemoryCatalogueRepository's
-- placeholder lists (app/repositories/memory/memory_catalogue_repository.py)
-- so nothing else in the app changes. Ids must stay stable if these rows
-- are ever replaced with better-researched content later.
--
-- Deliberately NOT seeded here:
--   - career_area: still pending real content from the AI role-prediction
--     work (has growth_outlook/evidence_source/source_date columns meant
--     for sourced data, not a plain placeholder list).
--   - break_reason: the break-reason field is being removed from the
--     wizard UI, so there is nothing to seed it for.

INSERT INTO experience_option (id, label) VALUES
  ('1', '1 year'),
  ('2', '2 years'),
  ('3', '3 years'),
  ('4', '4 years'),
  ('5', '5 years'),
  ('6', '6 years'),
  ('7', '7 years'),
  ('8', '8 years'),
  ('9', '9 years'),
  ('10_plus', '10+ years')
ON CONFLICT (id) DO NOTHING;

INSERT INTO responsibility (id, label) VALUES
  ('backend_development', 'Backend development'),
  ('api_design', 'API design'),
  ('debugging', 'Debugging & troubleshooting'),
  ('testing', 'Testing & QA'),
  ('code_review', 'Code review'),
  ('system_design', 'System design'),
  ('team_collaboration', 'Team collaboration'),
  ('project_delivery', 'Project delivery')
ON CONFLICT (id) DO NOTHING;

INSERT INTO return_status (id, label) VALUES
  ('ready', 'I''m ready to return'),
  ('preparing', 'I''m preparing to return'),
  ('planning_soon', 'I''m planning to return soon'),
  ('not_sure', 'I''m not sure yet')
ON CONFLICT (id) DO NOTHING;
