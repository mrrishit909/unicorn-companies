-- Today's list by first-listed country: the ten largest by total valuation (lower bound), everything else together.
WITH g AS (
    SELECT CASE WHEN country = '' THEN 'Not stated' ELSE country END AS country, COUNT(*) AS n, SUM(valuation) AS total_bn FROM cur GROUP BY 1
), r AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY total_bn DESC, country) AS rk FROM g
), x AS (
    SELECT CASE WHEN rk <= 10 THEN country ELSE 'All other' END AS country, MIN(rk) AS first_rk, CAST(SUM(n) AS BIGINT) AS n, SUM(total_bn) AS total_bn FROM r GROUP BY 1
)
SELECT country, n, ROUND(100.0 * n / SUM(n) OVER (), 1) AS share_n_pct, ROUND(total_bn, 1) AS total_bn, ROUND(100.0 * total_bn / SUM(total_bn) OVER (), 1) AS share_value_pct
FROM x ORDER BY first_rk;
