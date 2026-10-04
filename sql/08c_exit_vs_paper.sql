-- Former unicorns: the exit valuation (IPO, deal) against the last private valuation on the list. Only rows with both numbers exact (no "N+").
SELECT COALESCE(exit_class, 'All former') AS exit_class, COUNT(*) AS n_former, COUNT(*) FILTER (WHERE valuation IS NOT NULL AND NOT is_floor AND exit_valuation IS NOT NULL) AS n_both,
       COUNT(*) FILTER (WHERE valuation IS NOT NULL AND NOT is_floor AND exit_valuation < valuation) AS n_exit_below, COUNT(*) FILTER (WHERE valuation IS NOT NULL AND NOT is_floor AND exit_valuation > valuation) AS n_exit_above,
       ROUND(MEDIAN(exit_valuation / valuation) FILTER (WHERE NOT is_floor), 2) AS median_exit_over_last,
       ROUND(SUM(valuation) FILTER (WHERE NOT is_floor AND exit_valuation IS NOT NULL), 1) AS last_bn, ROUND(SUM(exit_valuation) FILTER (WHERE NOT is_floor AND valuation IS NOT NULL), 1) AS exit_bn
FROM cur_former GROUP BY ROLLUP (exit_class) ORDER BY exit_class NULLS LAST;
