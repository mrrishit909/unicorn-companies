-- The ten largest valuations on today's list, with their share of the total (lower bound) and the running share.
WITH r AS (
    SELECT company, valuation, is_floor, industry_group, country, val_year, ROW_NUMBER() OVER (ORDER BY valuation DESC, company) AS rk,
           SUM(valuation) OVER (ORDER BY valuation DESC, company) AS running, SUM(valuation) OVER () AS total
    FROM cur WHERE valuation IS NOT NULL
)
SELECT rk, company, valuation AS valuation_bn, ROUND(100.0 * valuation / total, 1) AS share_pct, ROUND(100.0 * running / total, 1) AS cumulative_pct, industry_group, country, val_year
FROM r WHERE rk <= 10 ORDER BY rk;
