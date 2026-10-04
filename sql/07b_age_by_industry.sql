-- Median age at the last listed valuation by industry group (groups with at least 8 usable founding years).
SELECT industry_group, COUNT(*) AS n_with_age, ROUND(MEDIAN(age), 1) AS median_age, MIN(age) AS youngest, MAX(age) AS oldest
FROM aged GROUP BY industry_group HAVING COUNT(*) >= 8 ORDER BY median_age, industry_group;
