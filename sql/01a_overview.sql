-- The list at three dates: how many companies, how many valuations are exact, how many are only "at least" (N+), and the total (a lower bound: floors count at their floor).
SELECT strftime(c.snap, '%Y-%m-%d') AS snapshot, c.n_listed, c.n_exact, c.n_floor, c.n_no_valuation, ROUND(c.total_bn, 1) AS total_bn, ROUND(c.floor_bn, 1) AS from_floors_bn,
       ROUND(c.median_exact, 2) AS median_exact_bn, f.n_former, c.n_listed + f.n_former AS ever_listed
FROM (SELECT snap, COUNT(*) AS n_listed, COUNT(*) FILTER (WHERE valuation IS NOT NULL AND NOT is_floor) AS n_exact, COUNT(*) FILTER (WHERE is_floor) AS n_floor,
             COUNT(*) FILTER (WHERE valuation IS NULL) AS n_no_valuation, SUM(valuation) AS total_bn, SUM(valuation) FILTER (WHERE is_floor) AS floor_bn,
             MEDIAN(valuation) FILTER (WHERE NOT is_floor) AS median_exact
      FROM li GROUP BY snap) c
JOIN (SELECT snap, COUNT(*) AS n_former FROM fo GROUP BY snap) f USING (snap)
ORDER BY c.snap;
