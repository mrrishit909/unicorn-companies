-- United States + China share of the list in each snapshot: by first-listed country and by "any mention" (a company listed as Israel / United States counts for both).
SELECT strftime(snap, '%Y-%m-%d') AS snapshot, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) FILTER (WHERE country = 'United States') / COUNT(*), 1) AS us_first_n_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE country = 'China') / COUNT(*), 1) AS china_first_n_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE country IN ('United States', 'China')) / COUNT(*), 1) AS us_china_first_n_pct,
       ROUND(100.0 * SUM(valuation) FILTER (WHERE country IN ('United States', 'China')) / SUM(valuation), 1) AS us_china_first_value_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE mentions_us OR mentions_china) / COUNT(*), 1) AS us_china_any_n_pct,
       ROUND(100.0 * SUM(valuation) FILTER (WHERE mentions_us OR mentions_china) / SUM(valuation), 1) AS us_china_any_value_pct,
       COUNT(*) FILTER (WHERE multi_country) AS n_multi_country
FROM li GROUP BY snap ORDER BY snap;
