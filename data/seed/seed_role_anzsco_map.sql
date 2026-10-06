

INSERT INTO role_anzsco_map (role_id, anzsco_code, confidence, rationale) VALUES
  ('blockchain_engineer', '2613', 'low', 'ANZSCO has no blockchain code; these roles are advertised as software engineers.'),
  ('business_intelligence_analyst', '2611', 'medium', 'BI roles are usually advertised as ICT Business Analyst, which sits in 2611.'),
  ('computer_and_information_research_scientist', '2611', 'low', 'No ANZSCO computing research code; 2611 is the nearest group.'),
  ('computer_and_information_systems_manager', '1351', 'high', 'Chief Information Officer and ICT Manager both sit in 1351.'),
  ('computer_network_architect', '2631', 'high', 'Network engineers and analysts sit in 2631 Computer Network Professionals.'),
  ('computer_network_support_specialist', '3131', 'medium', 'Network support technicians are in 3131; more senior support may sit in 2632.'),
  ('computer_programmer', '2613', 'high', 'Analyst Programmer and Developer Programmer sit in 2613.'),
  ('computer_systems_analyst', '2611', 'high', 'Systems Analyst is a named occupation in 2611.'),
  ('computer_systems_engineer_architect', '2631', 'medium', 'Systems engineering sits in 2631; solution architects also appear in 2611.'),
  ('computer_user_support_specialist', '3131', 'high', 'ICT Customer Support Officer (help desk) is a named occupation in 3131.'),
  ('data_scientist', '2611', 'low', 'ANZSCO 1.3 has no data scientist code; ads split between 2611 and statisticians.'),
  ('data_warehousing_specialist', '2621', 'medium', 'Warehousing is database work, so 2621, but no named occupation matches.'),
  ('database_administrator', '2621', 'high', 'Database Administrator is a named occupation in 2621.'),
  ('database_architect', '2621', 'high', 'Database work sits in 2621; ANZSCO has no separate database architect.'),
  ('digital_forensics_analyst', '2621', 'low', 'Counted under ICT Security Specialist; no separate code.'),
  ('information_security_analyst', '2621', 'medium', 'ICT Security Specialist is in 2621, shared with database and systems administrators.'),
  ('information_security_engineer', '2621', 'low', 'Counted under ICT Security Specialist; no separate engineer code.'),
  ('it_project_manager', '1351', 'medium', 'ICT Project Manager is in 1351, but the group also includes CIOs and ICT managers.'),
  ('network_and_systems_administrator', '2621', 'high', 'Systems Administrator is a named occupation in 2621.'),
  ('penetration_tester', '2621', 'low', 'Counted under ICT Security Specialist; no separate code.'),
  ('software_developer', '2613', 'high', 'Software Engineer and Developer Programmer both sit in 2613.'),
  ('software_qa_analyst_tester', '2632', 'medium', 'ICT Quality Assurance and Systems Test Engineers are in 2632, but the group also includes support engineers.'),
  ('telecommunications_engineering_specialist', '2633', 'high', 'Telecommunications engineers are a named group, 2633.'),
  ('video_game_designer', '2612', 'low', 'No ANZSCO game designer code; Multimedia Specialist in 2612 is the closest.'),
  ('web_administrator', '3131', 'high', 'Web Administrator is a named occupation in 3131 ICT Support Technicians.'),
  ('web_and_digital_interface_designer', '2324', 'medium', 'Web Designer sits in 2324; the group also includes graphic designers and illustrators.'),
  ('web_developer', '2612', 'high', 'Web Developer is a named occupation in 2612.')
ON CONFLICT (role_id) DO UPDATE SET
  anzsco_code = EXCLUDED.anzsco_code,
  confidence  = EXCLUDED.confidence,
  rationale   = EXCLUDED.rationale;
