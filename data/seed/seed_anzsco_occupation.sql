

INSERT INTO anzsco_occupation (code, title) VALUES
  ('1351', 'ICT Managers'),
  ('2324', 'Graphic and Web Designers, and Illustrators'),
  ('2611', 'ICT Business and Systems Analysts'),
  ('2612', 'Multimedia Specialists and Web Developers'),
  ('2613', 'Software and Applications Programmers'),
  ('2621', 'Database and Systems Administrators, and ICT Security Specialists'),
  ('2631', 'Computer Network Professionals'),
  ('2632', 'ICT Support and Test Engineers'),
  ('2633', 'Telecommunications Engineering Professionals'),
  ('3131', 'ICT Support Technicians')
ON CONFLICT (code) DO UPDATE SET title = EXCLUDED.title;
