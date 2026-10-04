-- Age at the LAST listed valuation (year of valuation - founding year) for the companies with a usable Wikidata founding year, by size of valuation.
-- Companies valued 1 to under 2 bn are the closest we get to "age when it became a unicorn": their last valuation is probably the round that crossed US$1 bn. Coverage shows who is missing.
WITH b AS (
    SELECT c.company, CASE WHEN c.valuation < 2 THEN '1: 1 to under 2 bn' WHEN c.valuation < 5 THEN '2: 2 to under 5 bn' ELSE '3: 5 bn and over' END AS bracket, a.age
    FROM cur c LEFT JOIN aged a USING (company) WHERE c.valuation IS NOT NULL
)
SELECT bracket, COUNT(*) AS n, COUNT(age) AS n_with_age, ROUND(100.0 * COUNT(age) / COUNT(*), 1) AS coverage_pct, ROUND(MEDIAN(age), 1) AS median_age,
       ROUND(100.0 * COUNT(*) FILTER (WHERE age <= 5) / COUNT(age), 1) AS pct_5_or_younger, ROUND(100.0 * COUNT(*) FILTER (WHERE age >= 10) / COUNT(age), 1) AS pct_10_or_older
FROM b GROUP BY bracket
UNION ALL
SELECT '0: all', COUNT(*), COUNT(age), ROUND(100.0 * COUNT(age) / COUNT(*), 1), ROUND(MEDIAN(age), 1), ROUND(100.0 * COUNT(*) FILTER (WHERE age <= 5) / COUNT(age), 1), ROUND(100.0 * COUNT(*) FILTER (WHERE age >= 10) / COUNT(age), 1) FROM b
ORDER BY 1;
