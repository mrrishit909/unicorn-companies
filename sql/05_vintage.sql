-- Year of the LAST valuation on today's list (not the year a company became a unicorn: the list has no such column).
SELECT val_year, COUNT(*) AS n, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_n_pct, COUNT(*) FILTER (WHERE is_floor) AS n_floor,
       ROUND(SUM(valuation), 1) AS total_bn, ROUND(100.0 * SUM(valuation) / SUM(SUM(valuation)) OVER (), 1) AS share_value_pct
FROM cur GROUP BY val_year ORDER BY val_year;
