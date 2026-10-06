



CREATE TABLE IF NOT EXISTS anzsco_occupation (
    code   VARCHAR(6) PRIMARY KEY,          
    title  TEXT NOT NULL                    
);



CREATE TABLE IF NOT EXISTS role_anzsco_map (
    role_id      VARCHAR(64) PRIMARY KEY             
                     REFERENCES role(id)             
                     ON DELETE CASCADE,              -- if a role is removed, its mapping goes too
    anzsco_code  VARCHAR(6) NOT NULL                 
                     REFERENCES anzsco_occupation(code),
    confidence   VARCHAR(10) NOT NULL                -- how good the match is
                     CHECK (confidence IN ('high', 'medium', 'low')),
    rationale    TEXT NOT NULL                       
);



-- ---- vacancy_monthly: JSA IVI ad counts ----
CREATE TABLE IF NOT EXISTS vacancy_monthly (
    anzsco_code  VARCHAR(6) NOT NULL                 -- FK: which ANZSCO group
                     REFERENCES anzsco_occupation(code),
    state        VARCHAR(4) NOT NULL,                
    month        DATE NOT NULL,                      -- first day of the month, e.g. 2026-08-01
    ads          NUMERIC(10,1) NOT NULL,             -- job ads 3 months avrage 
    PRIMARY KEY (anzsco_code, state, month)          
);

CREATE INDEX IF NOT EXISTS idx_vacancy_month ON vacancy_monthly(month);



CREATE OR REPLACE VIEW role_vacancy_latest AS
WITH latest AS (                                     -- the newest month in the table
    SELECT MAX(month) AS m FROM vacancy_monthly
),
stats AS (                                         
    SELECT
        v.anzsco_code,
        v.state,
        l.m AS latest_month,
        MAX(v.ads) FILTER (WHERE v.month = l.m)                          AS ads_latest,
        AVG(v.ads) FILTER (WHERE v.month >  l.m - INTERVAL '12 months')  AS ads_12m_avg,
        AVG(v.ads) FILTER (WHERE v.month <= l.m - INTERVAL '12 months'
                             AND v.month >  l.m - INTERVAL '24 months')  AS ads_prior_12m_avg
    FROM vacancy_monthly v
    CROSS JOIN latest l
    GROUP BY v.anzsco_code, v.state, l.m
)
SELECT
    r.id                                   AS role_id,
    r.label                                AS role_label,
    m.anzsco_code,
    o.title                                AS anzsco_title,
    m.confidence,
    s.state,
    s.latest_month,
    ROUND(s.ads_latest)::INT               AS ads_latest,       -- rounded for display
    ROUND(s.ads_12m_avg)::INT              AS ads_12m_avg,
    ROUND((s.ads_12m_avg - s.ads_prior_12m_avg)
          / NULLIF(s.ads_prior_12m_avg, 0) * 100, 1) AS yoy_change_pct   -- % change vs the year before
FROM role r
JOIN role_anzsco_map   m ON m.role_id     = r.id
JOIN anzsco_occupation o ON o.code        = m.anzsco_code
JOIN stats             s ON s.anzsco_code = m.anzsco_code;

