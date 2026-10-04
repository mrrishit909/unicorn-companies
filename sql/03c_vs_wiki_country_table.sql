-- The page's own "unicorns by country" table (CB Insights style count, includes companies that exited) against this list (current rows + former-unicorn rows), first-listed country.
WITH w AS (
    SELECT CASE country WHEN 'USA' THEN 'United States' WHEN 'UK' THEN 'United Kingdom' WHEN 'UAE' THEN 'United Arab Emirates' ELSE country END AS country, CAST(n_unicorns AS INTEGER) AS wiki_n
    FROM wiki_countries
), a AS (SELECT country, COUNT(*) AS list_now FROM cur GROUP BY country), b AS (SELECT country, COUNT(*) AS list_former FROM cur_former GROUP BY country)
SELECT w.country, w.wiki_n, COALESCE(a.list_now, 0) AS list_now, COALESCE(b.list_former, 0) AS list_former, COALESCE(a.list_now, 0) + COALESCE(b.list_former, 0) AS list_total,
       ROUND(100.0 * (COALESCE(a.list_now, 0) + COALESCE(b.list_former, 0)) / w.wiki_n, 1) AS list_total_pct_of_wiki_table
FROM w LEFT JOIN a USING (country) LEFT JOIN b USING (country)
ORDER BY w.wiki_n DESC, w.country LIMIT 10;
