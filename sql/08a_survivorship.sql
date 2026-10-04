-- What happened to the companies on the older lists: still listed, moved to the former-unicorns table (by recorded reason), or gone from both tables with no recorded reason.
-- A company that has two matches today counts once, by its first match.
SELECT strftime(snap, '%Y-%m-%d') AS snapshot, CASE WHEN n_now > 0 THEN '1: Still listed' WHEN n_former > 0 THEN '2: Former - ' || exit_class ELSE '3: Gone from both tables' END AS status,
       COUNT(*) AS n, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY snap), 1) AS share_n_pct, ROUND(SUM(valuation), 1) AS value_then_bn,
       ROUND(100.0 * SUM(valuation) / SUM(SUM(valuation)) OVER (PARTITION BY snap), 1) AS share_value_pct
FROM fate GROUP BY snap, status ORDER BY snap, status;
