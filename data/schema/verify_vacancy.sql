

-- 1. Row counts. Expect: 10 | 27 | 22140
SELECT (SELECT COUNT(*) FROM anzsco_occupation) AS occupations,
       (SELECT COUNT(*) FROM role_anzsco_map)   AS mappings,
       (SELECT COUNT(*) FROM vacancy_monthly)   AS vacancy_rows;


SELECT r.id FROM role r
LEFT JOIN role_anzsco_map m ON m.role_id = r.id
WHERE m.role_id IS NULL;

SELECT MAX(month) FROM vacancy_monthly;

-- evry role and the figures 
SELECT role_label, anzsco_code, confidence, ads_latest, ads_12m_avg, yoy_change_pct
FROM role_vacancy_latest
WHERE state = 'AUST'
ORDER BY ads_latest DESC;

-- one it role across all teh states 
SELECT state, ads_latest FROM role_vacancy_latest
WHERE role_id = 'software_developer'
ORDER BY ads_latest DESC;
