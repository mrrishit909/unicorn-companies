-- How old the last valuation is on 2026-10-02 (months from the valuation month; year-only dates count as June). Bands of whole years.
WITH b AS (
    SELECT CASE WHEN months_old <= 12 THEN '1: up to 1 year' WHEN months_old <= 24 THEN '2: 1-2 years' WHEN months_old <= 36 THEN '3: 2-3 years'
                WHEN months_old <= 60 THEN '4: 3-5 years' ELSE '5: over 5 years' END AS band, valuation, is_floor
    FROM cur
)
SELECT band, COUNT(*) AS n, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_n_pct, ROUND(SUM(valuation), 1) AS total_bn,
       ROUND(100.0 * SUM(valuation) / SUM(SUM(valuation)) OVER (), 1) AS share_value_pct, COUNT(*) FILTER (WHERE is_floor) AS n_floor
FROM b GROUP BY band ORDER BY band;
