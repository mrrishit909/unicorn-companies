-- The 451-ish companies on the December 2021 list that are still listed: has their valuation been updated since? Compared only when both valuations are exact (not "N+").
-- Companies with two matches today are left out (counted in the last row).
WITH m AS (
    SELECT o.company, o.valuation AS v_then, o.is_floor AS floor_then, o.val_year AS y_then, o.val_month AS m_then,
           (SELECT MIN(c.valuation) FROM cur c WHERE c.nname = o.nname OR (o.link <> '' AND c.link = o.link)) AS v_now,
           (SELECT BOOL_OR(c.is_floor) FROM cur c WHERE c.nname = o.nname OR (o.link <> '' AND c.link = o.link)) AS floor_now,
           (SELECT MIN(c.val_year) FROM cur c WHERE c.nname = o.nname OR (o.link <> '' AND c.link = o.link)) AS y_now,
           (SELECT MIN(c.val_month) FROM cur c WHERE c.nname = o.nname OR (o.link <> '' AND c.link = o.link)) AS m_now
    FROM fate o WHERE o.rev = 1062932765 AND o.n_now = 1
), k AS (
    SELECT *, CASE WHEN y_then IS NOT DISTINCT FROM y_now AND m_then IS NOT DISTINCT FROM m_now THEN '1: Same valuation date (not re-priced)'
                   WHEN floor_then OR floor_now OR v_then IS NULL OR v_now IS NULL THEN '5: Re-priced, but a floor ("N+") is involved'
                   WHEN v_now > v_then THEN '2: Re-priced higher' WHEN v_now < v_then THEN '3: Re-priced lower' ELSE '4: Re-priced, same value' END AS outcome
    FROM m
)
SELECT outcome, COUNT(*) AS n, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct, ROUND(MEDIAN(v_now / v_then), 2) AS median_ratio_now_to_then,
       ROUND(SUM(v_then), 1) AS value_then_bn, ROUND(SUM(v_now), 1) AS value_now_bn
FROM k GROUP BY outcome ORDER BY outcome;
