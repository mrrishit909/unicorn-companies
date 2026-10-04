-- Age at the last listed valuation in bands (years).
SELECT CASE WHEN age <= 2 THEN '1: 0-2' WHEN age <= 5 THEN '2: 3-5' WHEN age <= 8 THEN '3: 6-8' WHEN age <= 11 THEN '4: 9-11' WHEN age <= 15 THEN '5: 12-15' ELSE '6: 16-30' END AS band,
       COUNT(*) AS n, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct
FROM aged GROUP BY band ORDER BY band;
