-- Today's list by industry group: companies, total valuation (lower bound), shares, the median of the exact valuations, and how many valuations are only a floor.
WITH g AS (
    SELECT industry_group, COUNT(*) AS n, SUM(valuation) AS total_bn, MEDIAN(valuation) FILTER (WHERE NOT is_floor) AS median_exact, COUNT(*) FILTER (WHERE is_floor) AS n_floor
    FROM cur GROUP BY industry_group
)
SELECT industry_group, n, ROUND(100.0 * n / SUM(n) OVER (), 1) AS share_n_pct, ROUND(total_bn, 1) AS total_bn, ROUND(100.0 * total_bn / SUM(total_bn) OVER (), 1) AS share_value_pct,
       ROUND(median_exact, 2) AS median_exact_bn, n_floor, ROUND(100.0 * n_floor / n, 1) AS floor_pct
FROM g ORDER BY total_bn DESC, industry_group;
