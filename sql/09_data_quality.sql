-- Audit of the parsed tables (what the page's editors left messy).
SELECT k, what, n FROM (
    SELECT 1 AS k, 'rows in the current list (2026-10-02)' AS what, COUNT(*) AS n FROM cur
    UNION ALL SELECT 2, 'rows in the current former-unicorns table', COUNT(*) FROM cur_former
    UNION ALL SELECT 3, 'current rows with an exact valuation', COUNT(*) FROM cur WHERE valuation IS NOT NULL AND NOT is_floor
    UNION ALL SELECT 4, 'current rows with only a floor ("N+") or a range', COUNT(*) FROM cur WHERE is_floor
    UNION ALL SELECT 5, 'current rows whose floor is exactly "1+"', COUNT(*) FROM cur WHERE is_floor AND valuation = 1
    UNION ALL SELECT 6, 'current rows without any valuation number', COUNT(*) FROM cur WHERE valuation IS NULL
    UNION ALL SELECT 7, 'current rows with a blank industry', COUNT(*) FROM cur WHERE industry_group = 'Not stated'
    UNION ALL SELECT 8, 'current rows with a blank country', COUNT(*) FROM cur WHERE country = ''
    UNION ALL SELECT 9, 'current rows with several countries (/, comma, "and")', COUNT(*) FROM cur WHERE multi_country
    UNION ALL SELECT 10, 'current rows whose valuation date is a year only', COUNT(*) FROM cur WHERE val_month IS NULL
    UNION ALL SELECT 11, 'current rows with no link to a Wikipedia article', COUNT(*) FROM cur WHERE link = ''
    UNION ALL SELECT 12, 'distinct industry labels in the current list', COUNT(DISTINCT industry_raw) FROM listed WHERE rev = '1378068558'
    UNION ALL SELECT 13, 'current rows with a usable founding year', COUNT(*) FROM aged
    UNION ALL SELECT 14, 'founding years rejected (age outside 0-30: wrong article)', (SELECT COUNT(*) FROM cur c JOIN fd d ON c.link <> '' AND c.link = d.link WHERE d.founded_year IS NOT NULL) - (SELECT COUNT(*) FROM aged)
    UNION ALL SELECT 15, 'rows repaired by hand across the three snapshots (fix column)', (SELECT COUNT(*) FROM listed WHERE fix <> '') + (SELECT COUNT(*) FROM former WHERE fix <> '')
    UNION ALL SELECT 16, 'company names that appear twice in the current list', (SELECT COUNT(*) FROM (SELECT nname FROM cur GROUP BY nname HAVING COUNT(*) > 1))
    UNION ALL SELECT 17, 'companies in both current tables (listed and former)', (SELECT COUNT(*) FROM cur c WHERE EXISTS (SELECT 1 FROM cur_former f WHERE f.nname = c.nname))
    UNION ALL SELECT 18, 'former rows whose last valuation is dated after the exit', COUNT(*) FROM cur_former WHERE val_year * 12 + COALESCE(val_month, 6) > exit_year * 12 + COALESCE(exit_month, 6)
    UNION ALL SELECT 19, 'former rows without an exit valuation', COUNT(*) FROM cur_former WHERE exit_valuation IS NULL
    UNION ALL SELECT 20, 'former rows without a recorded exit reason', COUNT(*) FROM cur_former WHERE exit_class = 'Reason not stated'
) ORDER BY k;
