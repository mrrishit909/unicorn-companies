-- Stale = last valuation at least 36 months old on 2026-10-02. By industry group: companies, stale companies, and the share of the group's total valuation that is stale.
SELECT industry_group, COUNT(*) AS n, COUNT(*) FILTER (WHERE months_old >= 36) AS n_stale, ROUND(100.0 * COUNT(*) FILTER (WHERE months_old >= 36) / COUNT(*), 1) AS stale_pct,
       ROUND(100.0 * SUM(valuation) FILTER (WHERE months_old >= 36) / SUM(valuation), 1) AS stale_value_pct, ROUND(MEDIAN(months_old), 1) AS median_months
FROM cur GROUP BY industry_group ORDER BY stale_pct DESC, industry_group;
