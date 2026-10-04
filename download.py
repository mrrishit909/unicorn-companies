"""Step 1: fetch Wikipedia's "List of unicorn startup companies" (three pinned revisions) through the MediaWiki API, parse its two tables, and get
founding years from Wikidata for the companies that have a Wikipedia article.

    ./venv/bin/python download.py   -> data/rev_<id>.json (raw API answers, NOT committed), data/wikidata_*.json (raw, NOT committed),
                                       parsed/listed.csv, parsed/former.csv, parsed/founding.csv (small parsed tables, committed), results/pull.json

Source: https://en.wikipedia.org/wiki/List_of_unicorn_startup_companies, edited by volunteers. Licence CC BY-SA 4.0 (text of Wikipedia); the parsed tables in parsed/
keep that licence (attribution: "List of unicorn startup companies", Wikipedia contributors, revisions below; ShareAlike). Founding years: Wikidata property P571
(inception), Wikidata data is CC0. Founder names are NOT kept: only company names, valuations, industry, country and dates.
Snapshots (action=parse&oldid=...): 1062932765 (2021-12-31), 1192312891 (2023-12-28), 1378068558 (2026-10-02, the newest when this was built).
Wikimedia asks for one request at a time and a descriptive User-Agent: a file that is already on disk is never fetched again.
"""
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi
import ssl
from lxml import html

HERE = Path(__file__).parent
CTX = ssl.create_default_context(cafile=certifi.where())
UA = "research-portfolio (Rishit Raj Mathur; https://github.com/mrrishit909/unicorn-companies)"
WP = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"
SNAPS = {1062932765: "2021-12-31", 1192312891: "2023-12-28", 1378068558: "2026-10-02"}   # revid -> timestamp date of that revision
NOW = 1378068558
MONTHS = {m: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())}


def get(url, tries=8):
    """one polite request: retries with back-off, honours Retry-After (the rate limit answers with a text page, not JSON)"""
    wait = 10
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            body = urllib.request.urlopen(req, context=CTX, timeout=120).read()
            return json.loads(body)
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get("Retry-After") or wait)
        except ValueError:                                           # "You are making too many requests" came back with HTTP 200
            pass
        print(f"  rate-limited or bad answer, waiting {wait}s")
        time.sleep(wait)
        wait = min(wait * 2, 300)
    raise RuntimeError(f"gave up on {url}")


def fetch_revisions():
    for rev in SNAPS:
        f = HERE / "data" / f"rev_{rev}.json"
        if f.exists() and json.loads(f.read_text())["parse"]["revid"] == rev:
            continue
        d = get(f"{WP}?action=parse&oldid={rev}&prop=text&format=json&formatversion=2&disablelimitreport=1")
        f.write_text(json.dumps(d))
        time.sleep(5)


# ---------- parsing ----------
def cell_text(td):
    """text of a table cell without footnote markers, hidden date microformats and styles"""
    for bad in td.xpath(".//sup|.//style|.//*[contains(@style,'display: none')]"):
        bad.drop_tree()
    return re.sub(r"\s+", " ", td.text_content().replace("\xa0", " ")).strip()


def read_table(t):
    """rows of (cells as text, link title of the first cell, whether that link points to a missing page)"""
    out = []
    for tr in t.xpath(".//tr"):
        tds = tr.xpath("./td")
        if not tds:
            continue
        a = tds[0].xpath(".//a")
        link = None
        if a and "redlink=1" not in a[0].get("href", ""):
            href = a[0].get("href", "")
            link = urllib.parse.unquote(href.split("/wiki/", 1)[1].split("#")[0]).replace("_", " ") if "/wiki/" in href else None
        out.append(([cell_text(td) for td in tds], link))
    return out


def money(s):
    """'965' -> (965.0, False); '1+' -> (1.0, True) = at least; '80–90' -> (80.0, True) = low end of a range; '' -> (None, False)"""
    s = s.strip().replace(",", "")
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s), False
    m = re.fullmatch(r"(\d+(\.\d+)?)\+", s)
    if m:
        return float(m.group(1)), True
    m = re.fullmatch(r"(\d+(\.\d+)?)\s*[–-]\s*\d+(\.\d+)?", s)
    if m:
        return float(m.group(1)), True
    return None, False


def when(s):
    """year and month (month None when only a year is given) from 'May 2026', 'February 17, 2026', '26 January 2024', '2022'"""
    y = re.search(r"\b(19|20)\d\d\b", s)
    if not y:
        return None, None
    mo = next((MONTHS[w] for w in re.findall(r"[A-Za-z]+", s.lower()) if w in MONTHS), None)
    return int(y.group(0)), mo


def num(x):
    return "" if x is None else x


def parse_listed(rev, rows):
    out = []
    for cells, link in rows:
        cells, fix = (cells + [""] * 5)[:5], ""                         # a few rows lack trailing cells (founders) or carry empty extras: the first five are always the same
        if cells[0] == "Gong" and cells[3] == "June 2021":              # [Gong, 4.5, Nov 2025, 'June 2021' (stray date), 'Artificial intelligence', no country]
            cells, fix = [cells[0], cells[1], cells[2], cells[4], ""], "Gong: row shifted (stray date in the industry cell); industry read from the next cell, country missing"
        elif cells[0] == "Tujia.com" and cells[3] == "Justin Luo and Melissa Yang":   # founders sit in the industry cell
            cells, fix = [cells[0], cells[1], cells[2], "", cells[4]], "Tujia.com: founders' names in the industry cell; industry left empty"
        v, fl = money(cells[1])
        y, mo = when(cells[2])
        if cells[0]:                                                    # (a few empty spacer rows)
            out.append([rev, SNAPS[rev], cells[0], link or "", cells[1], num(v), int(fl), num(y), num(mo), cells[3], cells[4], fix])
    return out


def parse_former(rev, rows):
    """columns: company, last valuation, valuation date, exit date, exit reason, exit valuation, country. In the 2026 table two rows are misaligned (a cell lost in
    Nowports' row slid dLocal's numbers into it): handled by hand below and marked in the `fix` column; the audit lists them."""
    out = []
    for cells, link in rows:
        c, fix = cells[:7], ""
        if cells[0] == "Nowports" and len(cells) == 9:              # [name, 1.1, date, 'IPO' (in the exit-date cell), 'Logistics' (industry, in the reason cell), 5.0 (dLocal's), 'Uruguay / Mexico', founders, '']
            c, fix = [cells[0], cells[1], cells[2], "", cells[3], "", cells[6]], "Nowports: row shifted; exit date and exit valuation left empty, reason = the IPO written in the date cell"
        elif cells[0] == "dLocal" and len(cells) == 7:              # [name, 6.1, Apr 2021, Jun 2021, IPO, 'Uruguay', '']: last valuation 5.0 and exit valuation 6.1 as in the 2021 and 2023 revisions
            c, fix = [cells[0], "5.0", cells[2], cells[3], cells[4], cells[1], cells[5]], "dLocal: row lost a cell; 5.0 / 6.1 restored from the 2021 and 2023 revisions and the cited $5B source"
        c = (c + [""] * 7)[:7]
        if not c[0]:
            continue
        lv, lfl = money(c[1])
        ev, efl = money(c[5])
        vy, vm = when(c[2])
        xy, xm = when(c[3])
        out.append([rev, SNAPS[rev], c[0], link or "", c[1], num(lv), int(lfl), num(vy), num(vm), num(xy), num(xm), c[4], c[5], num(ev), c[6], fix])
    return out


def parse_all():
    listed, former = [], []
    for rev in SNAPS:
        root = html.fromstring(json.loads((HERE / "data" / f"rev_{rev}.json").read_text())["parse"]["text"])
        tabs = root.xpath("//table")
        # the list tables are the two whose header starts with "Company"
        comp = [t for t in tabs if t.xpath(".//th") and re.sub(r"\s+", " ", t.xpath(".//th")[0].text_content()).strip() == "Company"]
        assert len(comp) == 2, (rev, len(comp))
        listed += parse_listed(rev, read_table(comp[0]))
        former += parse_former(rev, read_table(comp[1]))
    return listed, former


# ---------- Wikidata (founding year) ----------
def founding(titles):
    """Wikipedia title -> Wikidata item (pageprops, 50 per call) -> inception P571 (50 per call). Raw answers cached in data/"""
    cache = HERE / "data" / "wikidata_raw.json"
    raw = json.loads(cache.read_text()) if cache.exists() else {"items": {}, "claims": {}}
    todo = [t for t in titles if t not in raw["items"]]
    for i in range(0, len(todo), 50):
        part = todo[i:i + 50]
        d = get(f"{WP}?action=query&prop=pageprops&ppprop=wikibase_item&redirects=1&format=json&formatversion=2&titles=" + urllib.parse.quote("|".join(part)))
        back = {}                                                    # normalised/redirected titles back to the asked ones
        for n in d["query"].get("normalized", []):
            back[n["to"]] = n["from"]
        for n in d["query"].get("redirects", []):
            back[n["to"]] = back.get(n["from"], n["from"])
        for p in d["query"]["pages"]:
            raw["items"][back.get(p["title"], p["title"])] = p.get("pageprops", {}).get("wikibase_item", "")
        for t in part:
            raw["items"].setdefault(t, "")
        cache.write_text(json.dumps(raw))
        time.sleep(5)
    ids = sorted({q for q in raw["items"].values() if q and q not in raw["claims"]})
    for i in range(0, len(ids), 50):
        part = ids[i:i + 50]
        d = get(f"{WD}?action=wbgetentities&props=claims&format=json&ids=" + "|".join(part))
        for q, e in d["entities"].items():
            raw["claims"][q] = [c["mainsnak"].get("datavalue", {}).get("value") for c in e.get("claims", {}).get("P571", [])]
        cache.write_text(json.dumps(raw))
        time.sleep(5)
    rows = []
    for t in titles:
        q = raw["items"].get(t, "")
        vals = [v for v in raw["claims"].get(q, []) if v]
        years = sorted({(int(v["time"][1:5]), v["precision"]) for v in vals if v["time"].startswith("+")})
        years = [y for y in years if y[1] >= 9]                     # precision 9 = year, 10 = month, 11 = day
        rows.append([t, q, years[0][0] if years else "", len(years)])
    return rows


def main():
    for d in ("data", "results", "parsed"):
        (HERE / d).mkdir(exist_ok=True)
    fetch_revisions()
    listed, former = parse_all()
    with open(HERE / "parsed" / "listed.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rev", "snapshot", "company", "link", "valuation_raw", "valuation", "is_floor", "val_year", "val_month", "industry_raw", "country_raw", "fix"])
        w.writerows(listed)
    with open(HERE / "parsed" / "former.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rev", "snapshot", "company", "link", "valuation_raw", "valuation", "is_floor", "val_year", "val_month", "exit_year", "exit_month", "exit_reason", "exit_valuation_raw", "exit_valuation", "country_raw", "fix"])
        w.writerows(former)
    root = html.fromstring(json.loads((HERE / "data" / f"rev_{NOW}.json").read_text())["parse"]["text"])
    tabs = root.xpath("//table")                                    # 0 = history of reported counts, 1 = unicorns by country (counting exits), 2 and 3 = the lists
    with open(HERE / "parsed" / "wiki_history.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n_unicorns", "total_valuation_bn", "date_text", "reported_by"])
        w.writerows([[c[0].replace(",", ""), c[1].replace(",", ""), c[2], c[3]] for c, _ in read_table(tabs[0])])
    with open(HERE / "parsed" / "wiki_countries.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["country", "n_unicorns", "per_million"])
        w.writerows([c[:3] for c, _ in read_table(tabs[1])])
    titles = sorted({r[3] for r in listed if r[0] == NOW and r[3]})
    f_rows = founding(titles)
    with open(HERE / "parsed" / "founding.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["link", "wikidata_item", "founded_year", "n_inception_values"])
        w.writerows(f_rows)
    files = {}
    for p in sorted((HERE / "data").glob("*.json")):
        b = p.read_bytes()
        files[p.name] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    info = {"pulled": date.today().isoformat(), "revisions": {str(k): v for k, v in SNAPS.items()}, "api": "action=parse&oldid=<rev>&prop=text; Wikidata wbgetentities P571",
            "rows": {"listed": len(listed), "former": len(former), "linked_titles_now": len(titles)}, "files": files}
    (HERE / "results" / "pull.json").write_text(json.dumps(info, indent=2) + "\n")
    print(json.dumps({k: v for k, v in info.items() if k != "files"}, indent=1))


if __name__ == "__main__":
    main()
