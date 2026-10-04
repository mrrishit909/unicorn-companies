"""Step 5: the project's check. Rebuild every result table with plain Python (csv, re, statistics, dictionaries and loops: no DuckDB, no SQL, no pandas) from the
stored parsed tables in parsed/ (and industry_rules.csv) and require every cell to equal what the SQL wrote to results/.

    ./venv/bin/python check.py

Numbers are compared at the precision the SQL rounded them to (half a unit in the last place); counts and text must match exactly.
The parsing of the Wikipedia HTML itself (download.py) is not re-done here: it is verified by the audit table 09 and by the row counts in results/pull.json.
"""
import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
R = HERE / "results"
P = HERE / "parsed"
NOW, Y21, Y23 = "1378068558", "1062932765", "1192312891"
n_ok = 0


def rd(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def num(x):
    return None if x == "" else float(x)


def ratio_pct(a, b):
    return 100.0 * a / b


def same(label, got, want, dec=None):
    """one cell: text exact, integers exact, floats within half a unit of the rounding the SQL used (dec decimals)"""
    global n_ok
    n_ok += 1
    if got is None or got == "":
        assert want in ("", None), f"{label}: recount empty, SQL {want!r}"
        return
    if isinstance(got, str):
        assert got == want, f"{label}: recount {got!r} != SQL {want!r}"
        return
    assert want not in ("", None), f"{label}: recount {got}, SQL empty"
    if dec is None:
        assert float(want) == got and float(want).is_integer(), f"{label}: recount {got} != SQL {want}"
    else:
        assert abs(got - float(want)) <= 0.5 * 10 ** (-dec) + 1e-9, f"{label}: recount {got} != SQL {want}"


def compare(name, rows, cols):
    """rows: list of lists in the column order of results/<name>.csv; cols: (column name, decimals or None) in that order"""
    want = rd(R / f"{name}.csv")
    assert len(rows) == len(want), f"{name}: {len(rows)} rows recounted, SQL has {len(want)}"
    for i, (mine, theirs) in enumerate(zip(rows, want)):
        assert list(theirs) == [c for c, _ in cols], f"{name}: columns {list(theirs)}"
        for (c, dec), m in zip(cols, mine):
            same(f"{name} row {i + 1} {c}", m, theirs[c], dec)


# ---------------------------------------------------------------- load
def country_text(c):
    c = re.sub(r"\bUSA\b|\bUS\b", "United States", c)
    c = re.sub(r"\bUK\b", "United Kingdom", c)
    c = re.sub(r"\bUAE\b", "United Arab Emirates", c)
    return re.sub(r"\s+", " ", c)


def first_country(c):
    c = re.sub(r"\s*\(.*\)", "", country_text(c))
    return re.sub(r"\s*(/|,| and ).*$", "", c).strip()


def nname(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load():
    rules = sorted(rd(HERE / "industry_rules.csv"), key=lambda r: int(r["priority"]))

    def group(raw):
        first = re.sub(r"\s*(/|,).*$", "", raw.lower()).strip()
        for r in rules:
            if re.search(r["pattern"], first):
                return r["industry_group"]
        return "Not stated" if first == "" else "Other / unspecified"

    L, F = [], []
    for r in rd(P / "listed.csv"):
        L.append({"rev": r["rev"], "snap": r["snapshot"], "company": r["company"], "link": r["link"], "nn": nname(r["company"]), "val": num(r["valuation"]),
                  "floor": r["is_floor"] == "1", "vy": None if r["val_year"] == "" else int(r["val_year"]), "vm": None if r["val_month"] == "" else int(r["val_month"]),
                  "raw": r["industry_raw"], "grp": group(r["industry_raw"]), "country": first_country(r["country_raw"]), "multi": bool(re.search(r"/|,| and ", r["country_raw"])),
                  "us": "united states" in country_text(r["country_raw"]).lower(), "cn": "china" in country_text(r["country_raw"]).lower(), "fix": r["fix"]})
    for x in L:
        x["months"] = None if x["vy"] is None else (2026 - x["vy"]) * 12 + (10 - (x["vm"] if x["vm"] is not None else 6))
    for r in rd(P / "former.csv"):
        reason = r["exit_reason"]
        if reason in ("IPO", "Direct listing", "SPAC merger", "Reverse takeover"):
            cls = "Listed (IPO, SPAC, direct)"
        elif reason in ("Acquired", "Acquisition", "IPO, Acquired", "Merger to GoTo", "Merge to GoTo") or reason.startswith("Acquired by"):
            cls = "Acquired or merged"
        elif reason in ("Defunct", "Bankruptcy", "Devalued", "Devaluation"):
            cls = "Failed or written down"
        else:
            cls = "Reason not stated"
        F.append({"rev": r["rev"], "snap": r["snapshot"], "company": r["company"], "link": r["link"], "nn": nname(r["company"]), "val": num(r["valuation"]), "floor": r["is_floor"] == "1",
                  "vy": None if r["val_year"] == "" else int(r["val_year"]), "vm": None if r["val_month"] == "" else int(r["val_month"]),
                  "xy": None if r["exit_year"] == "" else int(r["exit_year"]), "xm": None if r["exit_month"] == "" else int(r["exit_month"]),
                  "cls": cls, "xval": num(r["exit_valuation"]), "country": first_country(r["country_raw"]), "fix": r["fix"]})
    founding = {r["link"]: (None if r["founded_year"] == "" else int(r["founded_year"])) for r in rd(P / "founding.csv")}
    return L, F, founding


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def total(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) if xs else None


def pct(a, b):
    return None if a is None or b is None or b == 0 else 100.0 * a / b


def main():
    L, F, founding = load()
    cur = [x for x in L if x["rev"] == NOW]
    curF = [x for x in F if x["rev"] == NOW]
    snaps = [(Y21, "2021-12-31"), (Y23, "2023-12-28"), (NOW, "2026-10-02")]

    # aged: current rows with a usable founding year (matched by article link)
    aged = []
    for c in cur:
        if c["link"] != "" and c["link"] in founding and founding[c["link"]] is not None:
            age = c["vy"] - founding[c["link"]]
            if 0 <= age <= 30:
                aged.append({**c, "age": age})

    # ---- 01a overview
    rows = []
    for rev, d in snaps:
        s = [x for x in L if x["rev"] == rev]
        nf = len([x for x in F if x["rev"] == rev])
        exact = [x for x in s if x["val"] is not None and not x["floor"]]
        rows.append([d, len(s), len(exact), len([x for x in s if x["floor"]]), len([x for x in s if x["val"] is None]), total([x["val"] for x in s]),
                     total([x["val"] for x in s if x["floor"]]), med([x["val"] for x in s if not x["floor"]]), nf, len(s) + nf])
    compare("01a_overview", rows, [("snapshot", None), ("n_listed", None), ("n_exact", None), ("n_floor", None), ("n_no_valuation", None), ("total_bn", 1), ("from_floors_bn", 1),
                                   ("median_exact_bn", 2), ("n_former", None), ("ever_listed", None)])

    # ---- 01b CB Insights counts
    hist = [r for r in rd(P / "wiki_history.csv") if r["reported_by"] == "CB Insights" and r["date_text"] == "November 2025"]
    tot_now = total([x["val"] for x in cur])
    rows = [[h["date_text"], h["reported_by"], int(h["n_unicorns"]), float(h["total_valuation_bn"]), len(cur), tot_now, ratio_pct(len(cur), int(h["n_unicorns"])), ratio_pct(tot_now, float(h["total_valuation_bn"]))] for h in hist]
    compare("01b_vs_cbinsights", rows, [("date_text", None), ("reported_by", None), ("reported_n", None), ("reported_total_bn", 1), ("list_now_n", None), ("list_now_total_bn", 1),
                                        ("list_share_of_count_pct", 1), ("list_share_of_total_pct", 1)])

    # ---- 02a industry now
    by = defaultdict(list)
    for x in cur:
        by[x["grp"]].append(x)
    rows = []
    for g, xs in by.items():
        rows.append([g, len(xs), pct(len(xs), len(cur)), total([x["val"] for x in xs]), None, med([x["val"] for x in xs if not x["floor"]]), len([x for x in xs if x["floor"]]), pct(len([x for x in xs if x["floor"]]), len(xs))])
    all_total = total([r[3] for r in rows])
    for r in rows:
        r[4] = pct(r[3], all_total)
    rows.sort(key=lambda r: (-r[3], r[0]))
    compare("02a_industry_now", rows, [("industry_group", None), ("n", None), ("share_n_pct", 1), ("total_bn", 1), ("share_value_pct", 1), ("median_exact_bn", 2), ("n_floor", None), ("floor_pct", 1)])

    # ---- 02b growth
    groups = sorted({x["grp"] for x in L})
    rows = []
    for g in groups:
        n = {rev: len([x for x in L if x["rev"] == rev and x["grp"] == g]) for rev, _ in snaps}
        v = {rev: total([x["val"] for x in L if x["rev"] == rev and x["grp"] == g]) for rev, _ in snaps}
        rows.append([g, n[Y21], n[Y23], n[NOW], n[NOW] - n[Y21], n[NOW] - n[Y23], v[Y21], v[Y23], v[NOW], v[NOW] - v[Y21], v[NOW] / v[Y21], v[NOW] - v[Y23]])
    rows.sort(key=lambda r: (-r[9], r[0]))
    compare("02b_industry_growth", rows, [("industry_group", None), ("n_2021", None), ("n_2023", None), ("n_2026", None), ("n_change_since_2021", None), ("n_change_since_2023", None),
                                          ("value_2021_bn", 1), ("value_2023_bn", 1), ("value_2026_bn", 1), ("value_change_since_2021_bn", 1), ("value_ratio_2026_to_2021", 2),
                                          ("value_change_since_2023_bn", 1)])

    # ---- 03a country
    cc = defaultdict(lambda: [0, 0.0])
    for x in cur:
        k = x["country"] or "Not stated"
        cc[k][0] += 1
        cc[k][1] += x["val"] or 0.0
    ranked = sorted(cc.items(), key=lambda kv: (-kv[1][1], kv[0]))
    rows = [[k, v[0], None, v[1], None] for k, v in ranked[:10]]
    rows.append(["All other", sum(v[0] for _, v in ranked[10:]), None, sum(v[1] for _, v in ranked[10:]), None])
    for r in rows:
        r[2], r[4] = pct(r[1], len(cur)), pct(r[3], sum(rr[3] for rr in rows))
    compare("03a_country", rows, [("country", None), ("n", None), ("share_n_pct", 1), ("total_bn", 1), ("share_value_pct", 1)])

    # ---- 03b US + China
    rows = []
    for rev, d in snaps:
        s = [x for x in L if x["rev"] == rev]
        tv = total([x["val"] for x in s])
        us = [x for x in s if x["country"] == "United States"]
        cn = [x for x in s if x["country"] == "China"]
        both = [x for x in s if x["country"] in ("United States", "China")]
        anyx = [x for x in s if x["us"] or x["cn"]]
        rows.append([d, len(s), pct(len(us), len(s)), pct(len(cn), len(s)), pct(len(both), len(s)), pct(total([x["val"] for x in both]), tv), pct(len(anyx), len(s)),
                     pct(total([x["val"] for x in anyx]), tv), len([x for x in s if x["multi"]])])
    compare("03b_us_china", rows, [("snapshot", None), ("n", None), ("us_first_n_pct", 1), ("china_first_n_pct", 1), ("us_china_first_n_pct", 1), ("us_china_first_value_pct", 1),
                                   ("us_china_any_n_pct", 1), ("us_china_any_value_pct", 1), ("n_multi_country", None)])

    # ---- 03c vs the page's country table
    names = {"USA": "United States", "UK": "United Kingdom", "UAE": "United Arab Emirates"}
    w = [(names.get(r["country"], r["country"]), int(r["n_unicorns"])) for r in rd(P / "wiki_countries.csv")]
    w.sort(key=lambda t: (-t[1], t[0]))
    rows = []
    for c, n in w[:10]:
        a = len([x for x in cur if x["country"] == c])
        b = len([x for x in curF if x["country"] == c])
        rows.append([c, n, a, b, a + b, pct(a + b, n)])
    compare("03c_vs_wiki_country_table", rows, [("country", None), ("wiki_n", None), ("list_now", None), ("list_former", None), ("list_total", None), ("list_total_pct_of_wiki_table", 1)])

    # ---- 04a concentration
    rows = []
    for rev, d in snaps:
        s = sorted([x for x in L if x["rev"] == rev and x["val"] is not None], key=lambda x: (-x["val"], x["company"]))
        tv = sum(x["val"] for x in s)
        run, cum = 0.0, []
        for x in s:
            run += x["val"]
            cum.append(run)
        top = lambda k: pct(cum[k - 1], tv)
        half = next(i + 1 for i, c in enumerate(cum) if c >= 0.5 * tv)
        e80 = next(i + 1 for i, c in enumerate(cum) if c >= 0.8 * tv)
        rows.append([d, len(s), tv, top(1), top(5), top(10), top(20), top(50), top(100), half, e80])
    compare("04a_concentration", rows, [("snapshot", None), ("n", None), ("total_bn", 1), ("top1_pct", 1), ("top5_pct", 1), ("top10_pct", 1), ("top20_pct", 1), ("top50_pct", 1),
                                        ("top100_pct", 1), ("n_for_half", None), ("n_for_80pct", None)])

    # ---- 04b top 10
    s = sorted([x for x in cur if x["val"] is not None], key=lambda x: (-x["val"], x["company"]))
    tv = sum(x["val"] for x in s)
    rows, run = [], 0.0
    for i, x in enumerate(s[:10]):
        run += x["val"]
        rows.append([i + 1, x["company"], x["val"], pct(x["val"], tv), pct(run, tv), x["grp"], x["country"], x["vy"]])
    compare("04b_top10", rows, [("rk", None), ("company", None), ("valuation_bn", 2), ("share_pct", 1), ("cumulative_pct", 1), ("industry_group", None), ("country", None), ("val_year", None)])

    # ---- 05 vintage
    rows = []
    for y in sorted({x["vy"] for x in cur}):
        xs = [x for x in cur if x["vy"] == y]
        rows.append([y, len(xs), pct(len(xs), len(cur)), len([x for x in xs if x["floor"]]), total([x["val"] for x in xs]), pct(total([x["val"] for x in xs]), tot_now)])
    compare("05_vintage", rows, [("val_year", None), ("n", None), ("share_n_pct", 1), ("n_floor", None), ("total_bn", 1), ("share_value_pct", 1)])

    # ---- 06 stale
    def band(m):
        return "1: up to 1 year" if m <= 12 else "2: 1-2 years" if m <= 24 else "3: 2-3 years" if m <= 36 else "4: 3-5 years" if m <= 60 else "5: over 5 years"
    rows = []
    for b in sorted({band(x["months"]) for x in cur}):
        xs = [x for x in cur if band(x["months"]) == b]
        rows.append([b, len(xs), pct(len(xs), len(cur)), total([x["val"] for x in xs]), pct(total([x["val"] for x in xs]), tot_now), len([x for x in xs if x["floor"]])])
    compare("06a_stale", rows, [("band", None), ("n", None), ("share_n_pct", 1), ("total_bn", 1), ("share_value_pct", 1), ("n_floor", None)])

    rows = []
    for g, xs in by.items():
        st = [x for x in xs if x["months"] >= 36]
        rows.append([g, len(xs), len(st), pct(len(st), len(xs)), pct(total([x["val"] for x in st]), total([x["val"] for x in xs])), med([x["months"] for x in xs])])
    rows.sort(key=lambda r: (-r[3], r[0]))
    compare("06b_stale_by_industry", rows, [("industry_group", None), ("n", None), ("n_stale", None), ("stale_pct", 1), ("stale_value_pct", 1), ("median_months", 1)])

    st = [x for x in cur if x["months"] >= 36]
    fl = [x for x in cur if x["floor"]]
    ex = [x for x in cur if not x["floor"]]
    rows = [[len(cur), len(st), pct(len(st), len(cur)), pct(total([x["val"] for x in st]), tot_now), med([x["months"] for x in cur]), pct(len([x for x in fl if x["months"] >= 36]), len(fl)),
             pct(len([x for x in ex if x["months"] >= 36]), len(ex)), len([x for x in cur if x["vy"] == 2021]), pct(len([x for x in cur if x["vy"] == 2021]), len(cur))]]
    compare("06c_stale_summary", rows, [("n", None), ("n_stale", None), ("stale_pct", 1), ("stale_value_pct", 1), ("median_months", 1), ("stale_pct_among_floors", 1), ("stale_pct_among_exact", 1),
                                        ("n_2021", None), ("pct_2021", 1)])

    # ---- 07 age (07a joins on company name, like the SQL: one row per matching aged company)
    aged_by_name = defaultdict(list)
    for a in aged:
        aged_by_name[a["company"]].append(a["age"])
    recs = []
    for c in cur:
        if c["val"] is None:
            continue
        br = "1: 1 to under 2 bn" if c["val"] < 2 else "2: 2 to under 5 bn" if c["val"] < 5 else "3: 5 bn and over"
        for age in aged_by_name.get(c["company"], [None]):
            recs.append((br, age))

    def agerow(label, rs):
        ages = [a for _, a in rs if a is not None]
        return [label, len(rs), len(ages), pct(len(ages), len(rs)), med(ages), pct(len([a for a in ages if a <= 5]), len(ages)), pct(len([a for a in ages if a >= 10]), len(ages))]
    rows = [agerow("0: all", recs)] + [agerow(b, [r for r in recs if r[0] == b]) for b in ("1: 1 to under 2 bn", "2: 2 to under 5 bn", "3: 5 bn and over")]
    compare("07a_age_by_size", rows, [("bracket", None), ("n", None), ("n_with_age", None), ("coverage_pct", 1), ("median_age", 1), ("pct_5_or_younger", 1), ("pct_10_or_older", 1)])

    ag = defaultdict(list)
    for a in aged:
        ag[a["grp"]].append(a["age"])
    rows = [[g, len(v), med(v), min(v), max(v)] for g, v in ag.items() if len(v) >= 8]
    rows.sort(key=lambda r: (r[2], r[0]))
    compare("07b_age_by_industry", rows, [("industry_group", None), ("n_with_age", None), ("median_age", 1), ("youngest", None), ("oldest", None)])

    def aband(a):
        return "1: 0-2" if a <= 2 else "2: 3-5" if a <= 5 else "3: 6-8" if a <= 8 else "4: 9-11" if a <= 11 else "5: 12-15" if a <= 15 else "6: 16-30"
    cnt = defaultdict(int)
    for a in aged:
        cnt[aband(a["age"])] += 1
    rows = [[b, n, pct(n, len(aged))] for b, n in sorted(cnt.items())]
    compare("07c_age_histogram", rows, [("band", None), ("n", None), ("share_pct", 1)])

    # ---- 08 survivorship
    def matches(o, pool):
        return [c for c in pool if c["nn"] == o["nn"] or (o["link"] != "" and c["link"] == o["link"])]
    fate = []
    for o in L:
        if o["rev"] in (Y21, Y23):
            m_now = matches(o, cur)
            m_for = matches(o, curF)
            fate.append({**o, "n_now": len(m_now), "n_for": len(m_for), "cls": min((f["cls"] for f in m_for), default=None), "m_now": m_now})

    rows = []
    for rev, d in snaps[:2]:
        s = [o for o in fate if o["rev"] == rev]
        stat = defaultdict(list)
        for o in s:
            k = "1: Still listed" if o["n_now"] > 0 else ("2: Former - " + o["cls"]) if o["n_for"] > 0 else "3: Gone from both tables"
            stat[k].append(o)
        tv = total([o["val"] for o in s])
        for k in sorted(stat):
            v = total([o["val"] for o in stat[k]])
            rows.append([d, k, len(stat[k]), pct(len(stat[k]), len(s)), v, pct(v, tv)])
    compare("08a_survivorship", rows, [("snapshot", None), ("status", None), ("n", None), ("share_n_pct", 1), ("value_then_bn", 1), ("share_value_pct", 1)])

    outc = defaultdict(list)
    for o in fate:
        if o["rev"] != Y21 or o["n_now"] != 1:
            continue
        c = o["m_now"][0]
        if o["vy"] == c["vy"] and o["vm"] == c["vm"]:
            k = "1: Same valuation date (not re-priced)"
        elif o["floor"] or c["floor"] or o["val"] is None or c["val"] is None:
            k = '5: Re-priced, but a floor ("N+") is involved'
        elif c["val"] > o["val"]:
            k = "2: Re-priced higher"
        elif c["val"] < o["val"]:
            k = "3: Re-priced lower"
        else:
            k = "4: Re-priced, same value"
        outc[k].append((o["val"], c["val"]))
    nn_ = sum(len(v) for v in outc.values())
    rows = [[k, len(v), pct(len(v), nn_), med([b / a for a, b in v if a is not None and b is not None]), total([a for a, _ in v]), total([b for _, b in v])] for k, v in sorted(outc.items())]
    compare("08b_still_listed_repriced", rows, [("outcome", None), ("n", None), ("share_pct", 1), ("median_ratio_now_to_then", 2), ("value_then_bn", 1), ("value_now_bn", 1)])

    def exitrow(label, fs):
        both = [f for f in fs if f["val"] is not None and not f["floor"] and f["xval"] is not None]
        return [label, len(fs), len(both), len([f for f in both if f["xval"] < f["val"]]), len([f for f in both if f["xval"] > f["val"]]),
                med([f["xval"] / f["val"] for f in fs if not f["floor"] and f["xval"] is not None and f["val"] is not None]),
                total([f["val"] for f in fs if not f["floor"] and f["xval"] is not None]), total([f["xval"] for f in fs if not f["floor"] and f["val"] is not None])]
    classes = sorted({f["cls"] for f in curF} | {"All former"})
    rows = [exitrow("All former" if c == "All former" else c, curF if c == "All former" else [f for f in curF if f["cls"] == c]) for c in classes]
    compare("08c_exit_vs_paper", rows, [("exit_class", None), ("n_former", None), ("n_both", None), ("n_exit_below", None), ("n_exit_above", None), ("median_exit_over_last", 2), ("last_bn", 1), ("exit_bn", 1)])

    gone = sorted([o for o in fate if o["rev"] == Y21 and o["n_now"] == 0 and o["n_for"] == 0 and o["val"] is not None], key=lambda o: (-o["val"], o["company"]))[:10]
    compare("08d_gone_top10", [[o["company"], o["val"], o["country"], o["grp"]] for o in gone], [("company", None), ("valuation_2021_bn", 2), ("country", None), ("industry_group", None)])

    # ---- 09 data quality
    fixed = len([x for x in L if x["fix"]]) + len([x for x in F if x["fix"]])
    both_f = len([c for c in cur if any(f["nn"] == c["nn"] for f in curF)])
    nn_count = defaultdict(int)
    for c in cur:
        nn_count[c["nn"]] += 1
    usable_links = len([c for c in cur if c["link"] != "" and founding.get(c["link"]) is not None])
    after_exit = len([f for f in curF if f["vy"] is not None and f["xy"] is not None and f["vy"] * 12 + (f["vm"] if f["vm"] is not None else 6) > f["xy"] * 12 + (f["xm"] if f["xm"] is not None else 6)])
    items = [("rows in the current list (2026-10-02)", len(cur)), ("rows in the current former-unicorns table", len(curF)),
             ("current rows with an exact valuation", len([x for x in cur if x["val"] is not None and not x["floor"]])),
             ('current rows with only a floor ("N+") or a range', len([x for x in cur if x["floor"]])),
             ('current rows whose floor is exactly "1+"', len([x for x in cur if x["floor"] and x["val"] == 1])), ("current rows without any valuation number", len([x for x in cur if x["val"] is None])),
             ("current rows with a blank industry", len([x for x in cur if x["grp"] == "Not stated"])), ("current rows with a blank country", len([x for x in cur if x["country"] == ""])),
             ('current rows with several countries (/, comma, "and")', len([x for x in cur if x["multi"]])), ("current rows whose valuation date is a year only", len([x for x in cur if x["vm"] is None])),
             ("current rows with no link to a Wikipedia article", len([x for x in cur if x["link"] == ""])), ("distinct industry labels in the current list", len({x["raw"] for x in cur})),
             ("current rows with a usable founding year", len(aged)), ("founding years rejected (age outside 0-30: wrong article)", usable_links - len(aged)),
             ("rows repaired by hand across the three snapshots (fix column)", fixed), ("company names that appear twice in the current list", len([k for k, v in nn_count.items() if v > 1])),
             ("companies in both current tables (listed and former)", both_f), ("former rows whose last valuation is dated after the exit", after_exit),
             ("former rows without an exit valuation", len([f for f in curF if f["xval"] is None])), ("former rows without a recorded exit reason", len([f for f in curF if f["cls"] == "Reason not stated"]))]
    compare("09_data_quality", [[i + 1, w_, n] for i, (w_, n) in enumerate(items)], [("k", None), ("what", None), ("n", None)])

    # ---- the pull record agrees with the parsed files
    import json
    info = json.loads((R / "pull.json").read_text())
    for rev, d in snaps:
        assert info["revisions"][rev] == d
    same("pull.json listed rows", len(L), info["rows"]["listed"])
    same("pull.json former rows", len(F), info["rows"]["former"])
    print(f"check.py: {n_ok} recomputed numbers agree with results/")


if __name__ == "__main__":
    main()
