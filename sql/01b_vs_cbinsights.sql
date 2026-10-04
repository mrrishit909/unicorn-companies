-- The page's own history table (counts reported by CB Insights and others) next to the list: the list is a subset of what those counts describe.
SELECT h.date_text, h.reported_by, CAST(h.n_unicorns AS INTEGER) AS reported_n, TRY_CAST(h.total_valuation_bn AS DOUBLE) AS reported_total_bn,
       (SELECT COUNT(*) FROM cur) AS list_now_n, ROUND((SELECT SUM(valuation) FROM cur), 1) AS list_now_total_bn,
       ROUND(100.0 * (SELECT COUNT(*) FROM cur) / CAST(h.n_unicorns AS INTEGER), 1) AS list_share_of_count_pct,
       ROUND(100.0 * (SELECT SUM(valuation) FROM cur) / TRY_CAST(h.total_valuation_bn AS DOUBLE), 1) AS list_share_of_total_pct
FROM wiki_history h
WHERE h.reported_by = 'CB Insights' AND h.date_text = 'November 2025';
