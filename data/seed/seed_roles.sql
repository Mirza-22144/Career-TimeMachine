-- Seed: role table
-- Source: O*NET-SOC IT occupations (CC BY 4.0)


INSERT INTO role (id, label) VALUES
  ('blockchain_engineer', 'Blockchain Engineer'),
  ('business_intelligence_analyst', 'Business Intelligence Analyst'),
  ('computer_and_information_research_scientist', 'Computer and Information Research Scientist'),
  ('computer_and_information_systems_manager', 'Computer and Information Systems Manager'),
  ('computer_network_architect', 'Computer Network Architect'),
  ('computer_network_support_specialist', 'Computer Network Support Specialist'),
  ('computer_programmer', 'Computer Programmer'),
  ('computer_systems_analyst', 'Computer Systems Analyst'),
  ('computer_systems_engineer_architect', 'Computer Systems Engineer / Architect'),
  ('computer_user_support_specialist', 'Computer User Support Specialist'),
  ('data_scientist', 'Data Scientist'),
  ('data_warehousing_specialist', 'Data Warehousing Specialist'),
  ('database_administrator', 'Database Administrator'),
  ('database_architect', 'Database Architect'),
  ('digital_forensics_analyst', 'Digital Forensics Analyst'),
  ('information_security_analyst', 'Information Security Analyst'),
  ('information_security_engineer', 'Information Security Engineer'),
  ('it_project_manager', 'IT Project Manager'),
  ('network_and_systems_administrator', 'Network and Systems Administrator'),
  ('other', 'Other'),
  ('penetration_tester', 'Penetration Tester'),
  ('software_developer', 'Software Developer'),
  ('software_qa_analyst_tester', 'Software QA Analyst / Tester'),
  ('telecommunications_engineering_specialist', 'Telecommunications Engineering Specialist'),
  ('video_game_designer', 'Video Game Designer'),
  ('web_administrator', 'Web Administrator'),
  ('web_and_digital_interface_designer', 'Web and Digital Interface Designer'),
  ('web_developer', 'Web Developer')
ON CONFLICT (id) DO UPDATE SET label = EXCLUDED.label;
