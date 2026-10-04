-- Setup (not exported): typed views over the parsed Wikipedia tables.
--  * industry_map: the list's 227 free-text industry labels -> 15 groups. The group comes from the FIRST-listed item of the label (text before the first "/" or ",")
--    and the first rule in industry_rules.csv (by priority) whose regular expression matches; blank labels are "Not stated", labels no rule matches are "Other / unspecified".
--  * country = the FIRST-listed country ("Israel / United States" -> Israel); a note in brackets is dropped; multi_country and mentions_us keep the rest of the information.
--  * valuation = US$ billions as printed; "N+" means "at least N" and "80-90" is read as its low end, both flagged is_floor, so every sum is a lower bound.
--  * founded = Wikidata inception year of the company's Wikipedia article; accepted only when 0 <= (year of the last valuation - founded) <= 30 (two links point to other things).
CREATE VIEW industry_map AS
WITH f AS (
    SELECT DISTINCT industry_raw, trim(regexp_replace(lower(industry_raw), '\s*(/|,).*$', '')) AS first_item FROM listed
), m AS (
    SELECT f.industry_raw, r.industry_group
    FROM f JOIN industry_rules r ON regexp_matches(f.first_item, r.pattern)
    QUALIFY row_number() OVER (PARTITION BY f.industry_raw ORDER BY CAST(r.priority AS INTEGER)) = 1
)
SELECT f.industry_raw, COALESCE(m.industry_group, CASE WHEN f.first_item = '' THEN 'Not stated' ELSE 'Other / unspecified' END) AS industry_group
FROM f LEFT JOIN m USING (industry_raw);

-- the 2021 revision writes US / UK / UAE: normalised to the long names before anything is derived from the country text
CREATE MACRO country_text(c) AS regexp_replace(regexp_replace(regexp_replace(regexp_replace(c, '\bUSA\b|\bUS\b', 'United States'), '\bUK\b', 'United Kingdom'), '\bUAE\b', 'United Arab Emirates'), '\s+', ' ');

CREATE VIEW li AS
SELECT CAST(l.rev AS BIGINT) AS rev, CAST(l.snapshot AS DATE) AS snap, l.company, l.link, regexp_replace(lower(l.company), '[^a-z0-9]', '', 'g') AS nname,
       TRY_CAST(l.valuation AS DOUBLE) AS valuation, l.is_floor = '1' AS is_floor, TRY_CAST(l.val_year AS INTEGER) AS val_year, TRY_CAST(l.val_month AS INTEGER) AS val_month,
       m.industry_group, country_text(l.country_raw) AS country_raw,
       trim(regexp_replace(regexp_replace(country_text(l.country_raw), '\s*\(.*\)', ''), '\s*(/|,| and ).*$', '')) AS country,
       regexp_matches(l.country_raw, '/|,| and ') AS multi_country, lower(country_text(l.country_raw)) LIKE '%united states%' AS mentions_us,
       lower(country_text(l.country_raw)) LIKE '%china%' AS mentions_china, l.fix,
       (CAST(2026 AS INTEGER) - TRY_CAST(l.val_year AS INTEGER)) * 12 + (10 - COALESCE(TRY_CAST(l.val_month AS INTEGER), 6)) AS months_old
FROM listed l JOIN industry_map m USING (industry_raw);

CREATE VIEW fo AS
SELECT CAST(rev AS BIGINT) AS rev, CAST(snapshot AS DATE) AS snap, company, link, regexp_replace(lower(company), '[^a-z0-9]', '', 'g') AS nname,
       TRY_CAST(valuation AS DOUBLE) AS valuation, is_floor = '1' AS is_floor, TRY_CAST(val_year AS INTEGER) AS val_year, TRY_CAST(val_month AS INTEGER) AS val_month,
       TRY_CAST(exit_year AS INTEGER) AS exit_year, TRY_CAST(exit_month AS INTEGER) AS exit_month, exit_reason, TRY_CAST(exit_valuation AS DOUBLE) AS exit_valuation,
       country_text(country_raw) AS country_raw, trim(regexp_replace(regexp_replace(country_text(country_raw), '\s*\(.*\)', ''), '\s*(/|,| and ).*$', '')) AS country, fix,
       CASE WHEN exit_reason IN ('IPO', 'Direct listing', 'SPAC merger', 'Reverse takeover') THEN 'Listed (IPO, SPAC, direct)'
            WHEN exit_reason IN ('Acquired', 'Acquisition', 'IPO, Acquired', 'Merger to GoTo', 'Merge to GoTo') OR exit_reason LIKE 'Acquired by%' THEN 'Acquired or merged'
            WHEN exit_reason IN ('Defunct', 'Bankruptcy', 'Devalued', 'Devaluation') THEN 'Failed or written down'
            ELSE 'Reason not stated' END AS exit_class
FROM former;

CREATE VIEW cur AS SELECT * FROM li WHERE rev = 1378068558;
CREATE VIEW cur_former AS SELECT * FROM fo WHERE rev = 1378068558;

CREATE VIEW fd AS
SELECT link, TRY_CAST(founded_year AS INTEGER) AS founded_year FROM founding;

-- Today's companies with a usable founding year: age = year of the last valuation - founding year (whole years, so +-1).
CREATE VIEW aged AS
SELECT c.*, c.val_year - d.founded_year AS age
FROM cur c JOIN fd d ON c.link <> '' AND c.link = d.link
WHERE d.founded_year IS NOT NULL AND c.val_year - d.founded_year BETWEEN 0 AND 30;

-- Where each company of an older snapshot is today: matched by normalised name, or by article link when both have one.
CREATE VIEW fate AS
SELECT o.*, (SELECT COUNT(*) FROM cur c WHERE c.nname = o.nname OR (o.link <> '' AND c.link = o.link)) AS n_now,
       (SELECT COUNT(*) FROM cur_former f WHERE f.nname = o.nname OR (o.link <> '' AND f.link = o.link)) AS n_former,
       (SELECT MIN(f.exit_class) FROM cur_former f WHERE f.nname = o.nname OR (o.link <> '' AND f.link = o.link)) AS exit_class
FROM li o WHERE o.rev IN (1062932765, 1192312891);
