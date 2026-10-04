-- The ten largest companies on the December 2021 list that are in neither table today (reason not recorded on the page).
SELECT company, valuation AS valuation_2021_bn, country, industry_group
FROM fate WHERE rev = 1062932765 AND n_now = 0 AND n_former = 0 AND valuation IS NOT NULL
ORDER BY valuation DESC, company LIMIT 10;
