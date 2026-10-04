-- Which industries grew on the list: companies and total valuation (lower bound) per group in the three snapshots, and the change since December 2021 and December 2023.
-- Growth ON THE LIST: additions minus removals, not growth of the industry (groups come from the free-text labels; "Not stated" is its own row because blank labels are mostly recent rows).
WITH t AS (
    SELECT industry_group,
           COUNT(*) FILTER (WHERE rev = 1062932765) AS n_2021, COUNT(*) FILTER (WHERE rev = 1192312891) AS n_2023, COUNT(*) FILTER (WHERE rev = 1378068558) AS n_2026,
           SUM(valuation) FILTER (WHERE rev = 1062932765) AS v_2021, SUM(valuation) FILTER (WHERE rev = 1192312891) AS v_2023, SUM(valuation) FILTER (WHERE rev = 1378068558) AS v_2026
    FROM li GROUP BY industry_group
)
SELECT industry_group, n_2021, n_2023, n_2026, n_2026 - n_2021 AS n_change_since_2021, n_2026 - n_2023 AS n_change_since_2023,
       ROUND(v_2021, 1) AS value_2021_bn, ROUND(v_2023, 1) AS value_2023_bn, ROUND(v_2026, 1) AS value_2026_bn,
       ROUND(v_2026 - v_2021, 1) AS value_change_since_2021_bn, ROUND(v_2026 / v_2021, 2) AS value_ratio_2026_to_2021, ROUND(v_2026 - v_2023, 1) AS value_change_since_2023_bn
FROM t ORDER BY v_2026 - v_2021 DESC, industry_group;
