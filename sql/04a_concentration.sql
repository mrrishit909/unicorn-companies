-- Concentration of valuation on the list: the share of the total (lower bound) held by the top 1, 5, 10, 20, 50, 100 companies, and how many companies make up half and 80%.
-- Rank: valuation, largest first; ties by company name.
WITH r AS (
    SELECT rev, snap, company, valuation, ROW_NUMBER() OVER (PARTITION BY rev ORDER BY valuation DESC, company) AS rk,
           SUM(valuation) OVER (PARTITION BY rev ORDER BY valuation DESC, company) AS running, SUM(valuation) OVER (PARTITION BY rev) AS total
    FROM li WHERE valuation IS NOT NULL
)
SELECT strftime(snap, '%Y-%m-%d') AS snapshot, COUNT(*) AS n, ROUND(MAX(total), 1) AS total_bn,
       ROUND(100.0 * MAX(running) FILTER (WHERE rk = 1) / MAX(total), 1) AS top1_pct, ROUND(100.0 * MAX(running) FILTER (WHERE rk = 5) / MAX(total), 1) AS top5_pct,
       ROUND(100.0 * MAX(running) FILTER (WHERE rk = 10) / MAX(total), 1) AS top10_pct, ROUND(100.0 * MAX(running) FILTER (WHERE rk = 20) / MAX(total), 1) AS top20_pct,
       ROUND(100.0 * MAX(running) FILTER (WHERE rk = 50) / MAX(total), 1) AS top50_pct, ROUND(100.0 * MAX(running) FILTER (WHERE rk = 100) / MAX(total), 1) AS top100_pct,
       MIN(rk) FILTER (WHERE running >= 0.5 * total) AS n_for_half, MIN(rk) FILTER (WHERE running >= 0.8 * total) AS n_for_80pct
FROM r GROUP BY rev, snap ORDER BY snap;
