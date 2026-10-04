-- One row: how much of today's list is stale (36+ months) and how floor-only valuations compare.
SELECT COUNT(*) AS n, COUNT(*) FILTER (WHERE months_old >= 36) AS n_stale, ROUND(100.0 * COUNT(*) FILTER (WHERE months_old >= 36) / COUNT(*), 1) AS stale_pct,
       ROUND(100.0 * SUM(valuation) FILTER (WHERE months_old >= 36) / SUM(valuation), 1) AS stale_value_pct, ROUND(MEDIAN(months_old), 1) AS median_months,
       ROUND(100.0 * COUNT(*) FILTER (WHERE months_old >= 36 AND is_floor) / COUNT(*) FILTER (WHERE is_floor), 1) AS stale_pct_among_floors,
       ROUND(100.0 * COUNT(*) FILTER (WHERE months_old >= 36 AND NOT is_floor) / COUNT(*) FILTER (WHERE NOT is_floor), 1) AS stale_pct_among_exact,
       COUNT(*) FILTER (WHERE val_year = 2021) AS n_2021, ROUND(100.0 * COUNT(*) FILTER (WHERE val_year = 2021) / COUNT(*), 1) AS pct_2021
FROM cur;
