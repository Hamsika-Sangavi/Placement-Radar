-- Placement Radar: SQL used for the analysis (SQLite).
-- Tables: jobs, job_skills (job_id, skill), job_cities (job_id, city)
-- Run:  sqlite3 data/placement_radar.db < sql/queries.sql

-- 1. Top 15 skills overall, as a share of all postings
SELECT skill,
       COUNT(*)                                                    AS jobs,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM jobs), 1)    AS pct_of_jobs
FROM job_skills
GROUP BY skill
ORDER BY jobs DESC
LIMIT 15;

-- 2. Skill demand inside each role family, ranked with a window function
WITH role_skill AS (
    SELECT j.role_family, s.skill, COUNT(*) AS jobs
    FROM jobs j
    JOIN job_skills s USING (job_id)
    GROUP BY j.role_family, s.skill
),
role_total AS (
    SELECT role_family, COUNT(*) AS n FROM jobs GROUP BY role_family
)
SELECT r.role_family, r.skill, r.jobs,
       ROUND(100.0 * r.jobs / t.n, 1) AS pct_in_role,
       RANK() OVER (PARTITION BY r.role_family ORDER BY r.jobs DESC) AS rank_in_role
FROM role_skill r
JOIN role_total t USING (role_family)
WHERE t.n >= 100
ORDER BY r.role_family, rank_in_role
LIMIT 60;

-- 3. Hyderabad vs all cities: which skills are over-represented in Hyderabad postings?
WITH hyd AS (SELECT DISTINCT job_id FROM job_cities WHERE city = 'Hyderabad'),
hyd_n AS (SELECT COUNT(*) AS n FROM hyd),
all_n AS (SELECT COUNT(*) AS n FROM jobs),
hyd_skill AS (
    SELECT s.skill, COUNT(*) AS jobs FROM job_skills s JOIN hyd USING (job_id) GROUP BY s.skill
),
all_skill AS (
    SELECT skill, COUNT(*) AS jobs FROM job_skills GROUP BY skill
)
SELECT h.skill,
       ROUND(100.0 * h.jobs / (SELECT n FROM hyd_n), 1) AS pct_hyderabad,
       ROUND(100.0 * a.jobs / (SELECT n FROM all_n), 1) AS pct_all,
       ROUND(1.0 * (h.jobs * 1.0 / (SELECT n FROM hyd_n)) / (a.jobs * 1.0 / (SELECT n FROM all_n)), 2) AS lift
FROM hyd_skill h JOIN all_skill a USING (skill)
WHERE a.jobs >= 200
ORDER BY lift DESC
LIMIT 10;

-- 4. Fresher-friendly share by role family (experience minimum of 0 or 1 year)
SELECT role_family,
       COUNT(*)                                         AS jobs,
       SUM(is_fresher_friendly)                         AS fresher_jobs,
       ROUND(100.0 * AVG(is_fresher_friendly), 1)       AS fresher_pct
FROM jobs
GROUP BY role_family
ORDER BY fresher_pct DESC;

-- 5. Companies hiring freshers the most, with employee rating
SELECT company,
       SUM(is_fresher_friendly)        AS fresher_jobs,
       ROUND(AVG(company_rating), 1)   AS rating
FROM jobs
WHERE is_fresher_friendly = 1
GROUP BY company
HAVING fresher_jobs >= 5
ORDER BY fresher_jobs DESC
LIMIT 15;

-- 6. Skills that appear together most often (pairs) in fresher-friendly jobs
SELECT a.skill AS skill_a, b.skill AS skill_b, COUNT(*) AS jobs_together
FROM job_skills a
JOIN job_skills b ON a.job_id = b.job_id AND a.skill < b.skill
JOIN jobs j ON j.job_id = a.job_id
WHERE j.is_fresher_friendly = 1
GROUP BY a.skill, b.skill
ORDER BY jobs_together DESC
LIMIT 15;

-- 7. How much salary information is there? (the data is mostly "Not disclosed")
SELECT has_salary,
       COUNT(*) AS jobs,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM jobs), 1) AS pct
FROM jobs
GROUP BY has_salary;
