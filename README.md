# Do five companies hold half the unicorn value?

Wikipedia's "List of unicorn startup companies" (private companies valued at US$1 billion or more), read at three dates and analysed in SQL (DuckDB). Five questions:
- which industries and countries hold the value, and which industries grew fastest on the list;
- how concentrated the value is (the top 10 companies, the United States and China together);
- how many of the valuations are stale, and what share of the value they carry;
- how old the companies were at their last listed valuation;
- survivorship: what became of the companies on the older lists, and how exits compare with the "paper" valuations.

The questions follow DataCamp's "Analyzing Unicorn Companies" (SQL on CB Insights' file of unicorns, which is not open): the same columns (company, valuation, date, industry, country) from the open list. The page with the results and the charts is the build log:

Build log: https://mrrishit909.github.io/projects/unicorn-companies/

## Data

Wikipedia, "List of unicorn startup companies", fetched through the MediaWiki API (`action=parse`, no HTML crawling) at three pinned revisions: 1062932765 (31 Dec 2021), 1192312891 (28 Dec 2023) and 1378068558 (2 Oct 2026, the newest when this was built). Each has a list of current unicorns and a table of "former unicorns" (exited by IPO or acquisition). The page is edited by volunteers; text under CC BY-SA 4.0 (attribution: Wikipedia contributors; ShareAlike), so the small parsed tables in `parsed/` (company, valuation, dates, industry, country; no founder names) carry the same licence. Founding years come from Wikidata (property P571, CC0) for the 374 listed companies that have a Wikipedia article. The raw API answers (5.4 MB) are fetched by `download.py` (checksums in `results/pull.json`) and not committed.

```
./venv/bin/pip install pandas matplotlib duckdb lxml certifi      # in a venv
./venv/bin/python download.py    # data/* and parsed/*  (one request at a time, a few minutes if Wikimedia rate-limits)
./venv/bin/python run_sql.py     # results/*  (a second)
./venv/bin/python check.py       # a few seconds
./venv/bin/python charts.py
```

## Steps

1. **Download** the three revisions and the Wikidata founding years, then parse the two tables of each revision. Valuations are read as US$ billions; "N+" means "at least N" and the one range (Binance, 80-90) is read at its low end, so every total is a lower bound. Four rows that Wikipedia's own table had shifted by a cell (Gong, Tujia.com, Nowports, dLocal) are repaired by name and listed in the `fix` column.
2. **Audit** (`sql/09_data_quality.sql`): floors, blank labels, year-only dates, rows without an article, dates that fall after the exit.
3. **Group** the 179 free-text industry labels into 15 groups with the regular expressions in `industry_rules.csv` (first-listed item of the label, first matching rule); the first-listed country is the company's country.
4. **Analyse in SQL** (`sql/`, 21 queries, window functions and CTEs): industry, country, concentration, the age of each valuation, founding age, and survivorship by matching each company of an older revision to today's list and former-unicorns table (by name, or by article link).
5. **Check.** `check.py` recomputes every table from the parsed tables in plain Python (csv, re, statistics and loops: no DuckDB, no SQL, no pandas): 1,155 numbers.
6. **Charts.**

## Results

- **The list.** On 2 Oct 2026 it has 632 companies (and 209 former unicorns), worth at least $5.38 trillion in all. Only 468 valuations are exact; 164 are a floor ("1+", "5+"; 152 of them exactly "1+"), which add $257bn (4.8% of the total). The same page quotes CB Insights at 1,334 unicorns and $5.4 trillion in November 2025: this list holds 47% of those companies and almost the same total (99%), since its five largest alone are 51% of it (next bullet).
- **Five companies hold half.** The five largest (Anthropic, OpenAI, ByteDance, Databricks, Stripe) hold 51.4% of the total, the top 10 57.1% and the top 100 79.7%; the largest alone (Anthropic, $965bn) holds 17.9%. In December 2021 the top 10 held 24.7% and it took 60 companies to reach half; in December 2023 28.2% and 61. The sixth largest, Binance ($80bn), is valued as of 2021.
- **AI is 8.4% of the companies and 42.6% of the value** (53 companies, $2,291bn; its median exact valuation is $6.3bn). In December 2021 AI was 18 companies and 3.0% of the value; it added 35 companies since, more than any other group (fintech 15, software 12), while transport lost 10 and media and games 5. That is growth on the list (additions less removals), and the "Not stated" label fell from 97 to 49 companies, so part of every group's growth is labels being filled in.
- **The United States and China.** With the first-listed country, the United States has 36.7% of the companies and 64.5% of the value, China 9.7% and 14.6%; together 46.4% of the companies and 79.1% of the value (counting any mention, e.g. Israel / United States: 52.2% and 81.4%). The value share was 60.1% in 2021 and 63.5% in 2023, and the company share was 48.2% and 45.8%: the rise is in value, not in the number of companies.
- **Most valuations are old, and they are small.** 533 of 632 companies (84.3%) have a last valuation at least 36 months old (median age 62.0 months); together they are 29.1% of the total value. 295 companies (46.7%) were last valued in 2021 (the year with most valuations on the list), 95.1% of the floor-only valuations are stale, against 80.6% of the exact ones; the 53 companies valued in 2026 carry 60.3% of the value. By group the stale share runs from 30.2% (AI) to 100% (crypto, all 25 companies).
- **Age at the last listed valuation.** The list has no "date it became a unicorn" column, so years from founding to unicorn cannot be computed. For the 250 companies (39.6%) with a usable Wikidata founding year, the median is 8.0 years between founding and the last listed valuation (an upper bound on the age at which they became unicorns); 24.0% were 5 or younger and 36.0% 10 or older. For companies valued under US$2 billion, whose last round is probably the one that crossed US$1 billion, the median is 8.0 years (97 companies). AI is the youngest group (median 5.0 years, 19 companies), software the oldest (10.0, 53). Coverage is 29.4% for companies valued under $2 billion and 59.0% for those worth $5 billion or more, so the sample leans to the famous ones.
- **Survivorship: the list loses companies quietly.** Of the 595 companies on the December 2021 list, 451 (75.8%) are still listed, 13 (2.2%) are in the former-unicorns table (only 2 with a failure recorded) and 131 (22.0%, $519bn of their 2021 value) are in neither table, with no reason given. For December 2023 the figures are 79.0% still listed and 134 (20.0%) gone. The ten largest of the 2021 companies now gone are Klarna, Chime, FTX, Byju's, Trendyol, Brex, SenseTime, Northvolt, Aurora, Reddit; the page does not say whether they listed, were sold or failed. Of the 450 still-listed 2021 companies that could be matched one to one, 401 (89.1%) show the same valuation date as in 2021; of the re-priced ones with exact numbers 32 went up (median 2.25x) and 5 down (0.7x).
- **Exits against paper valuations.** For 173 of the 209 former unicorns both the last private valuation and the exit valuation are exact: 125 exited above and 36 below, with a median exit-to-last ratio of 1.44x (1.55x for listings, 1.06x for acquisitions). The 8 recorded failures have numbers for 3 (median 0.22x). Companies that vanished without an exit record are not in this comparison.
- **Counts of the list, not of the world.** The page's own country table (which counts exits) has 1,126 United States and 279 China unicorns; this list and its former table have 332 and 104. 4 rows were repaired by hand, 10 former-unicorn rows carry a last valuation dated after the exit, and 258 of 632 companies have no Wikipedia article.

## Not done, and caveats

- Wikipedia's list is edited by volunteers from news reports and mixes sources, dates and definitions; it is a snapshot of what editors recorded, not a census. Totals and shares are of the list, as of the revision used; later edits are not in them.
- A valuation is the last round's "paper" price, not what the shares would fetch; the list cites news reports for them; 26% of the current valuations are only a floor. Totals are lower bounds; the order of the top companies is as listed.
- The valuation date is the date of the last valuation, not the date the company became a unicorn: nothing here measures time to unicorn, the vintage and age results describe last valuations, and they are lower-resolution for companies whose date is a year only (9 rows, counted as June).
- Industry groups are my own regular expressions on free text and 49 current companies have no industry; country is the first-listed one. Growth by group is growth on the list (additions minus removals), partly relabelling.
- Founding years cover 250 of 632 companies (those with a Wikipedia article and an inception date on Wikidata); 3 implausible links (age outside 0-30 years) were dropped, and the age is a difference of calendar years (plus or minus one).
- "Gone from both tables" means not found by name or article link; renamed companies can be counted as gone, and a company is "still listed" if its name or link matches (two different firms named Alchemy would match each other). The reasons for removal are not recorded, so nothing is said about how many failed.
- The parsing of the HTML in `download.py` is checked by the audit and by the row counts, not re-done in `check.py`, which recounts from the parsed tables.
- Company names and valuations are public aggregates from the list as published; I did not check any valuation against its cited source.
