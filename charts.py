"""Step 6: charts.   ./venv/bin/python charts.py -> charts/00_cover.png, 01_industry.png, 02_concentration.png, 03_stale.png, 04_age.png, 05_survivors.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
R = HERE / "results"
INK, DIM, GRID, BG, BLUE, ORANGE, GRAY, GREEN = "#f2f2f0", "#8a8a87", "#1d1d1d", "#0b0b0b", "#3987e5", "#d95926", "#9a9a96", "#3aa876"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
                     "axes.edgecolor": "#3a3a3a", "axes.labelcolor": DIM, "xtick.color": DIM, "ytick.color": DIM,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 11, "axes.titlesize": 13,
                     "axes.titlelocation": "left", "axes.titlepad": 12})


def t(name):
    return pd.read_csv(R / f"{name}.csv")


IND, GROW, CTY, CON, VIN, ST, STS, AGE, AGEH, SUR, EXIT = (t("02a_industry_now"), t("02b_industry_growth"), t("03a_country"), t("04a_concentration"), t("05_vintage"), t("06a_stale"),
                                                            t("06c_stale_summary"), t("07b_age_by_industry"), t("07c_age_histogram"), t("08a_survivorship"), t("08c_exit_vs_paper"))
SIZE = t("07a_age_by_size")
TOPS = ["top1_pct", "top5_pct", "top10_pct", "top20_pct", "top50_pct", "top100_pct"]
TOPN = [1, 5, 10, 20, 50, 100]
SNAPS = ["2021-12-31", "2023-12-28", "2026-10-02"]
SNAPCOL = {"2021-12-31": "#5a5a58", "2023-12-28": GRAY, "2026-10-02": BLUE}


def save(fig, name):
    fig.tight_layout(); fig.savefig(HERE / "charts" / name, dpi=150); plt.close(fig)


def short(s):
    return s.replace("Hardware, energy & telecom", "Hardware, energy, telecom").replace("Food, travel & hospitality", "Food, travel, hospitality").replace("Real estate & construction", "Real estate, construction")


def top_curve(ax, snaps=SNAPS, fs=9):
    for s in snaps:
        r = CON[CON["snapshot"] == s].iloc[0]
        ax.plot(TOPN, [r[c] for c in TOPS], marker="o", markersize=5, linewidth=2.4 if s == "2026-10-02" else 1.6, color=SNAPCOL[s], label=s[:7].replace("-12", " (Dec)").replace("-10", " (Oct)"))
    r = CON[CON["snapshot"] == "2026-10-02"].iloc[0]
    for n, c in zip(TOPN, TOPS):
        if n in (5, 10, 100):
            ax.annotate(f"{r[c]:.0f}%", (n, r[c]), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=fs, color=INK)
    ax.set_xscale("log"); ax.set_xticks(TOPN); ax.set_xticklabels([str(n) for n in TOPN]); ax.minorticks_off(); ax.set_ylim(0, 100)
    ax.set_xlabel("the N largest companies (log scale)"); ax.set_ylabel("share of the list's total valuation (%)"); ax.legend(frameon=False, labelcolor=INK, fontsize=fs, loc="lower right", title="list as of", title_fontsize=fs)


def stale_bars(ax, fs=9):
    x = np.arange(len(ST)); w = 0.38
    ax.bar(x - w / 2, ST["share_n_pct"], width=w * 0.92, color=GRAY, label="share of companies"); ax.bar(x + w / 2, ST["share_value_pct"], width=w * 0.92, color=BLUE, label="share of total valuation")
    for xi, v in list(zip(x - w / 2, ST["share_n_pct"])) + list(zip(x + w / 2, ST["share_value_pct"])):
        ax.text(xi, v + 1, f"{v:.0f}", ha="center", fontsize=fs, color=INK)
    ax.set_xticks(x); ax.set_xticklabels(["under 1\nyear", "1-2", "2-3", "3-5", "over 5\nyears"], fontsize=9); ax.set_ylim(0, 85); ax.grid(axis="x", visible=False)
    ax.set_xlabel("age of the last valuation on 2 Oct 2026"); ax.set_ylabel("%"); ax.legend(frameon=False, labelcolor=INK, fontsize=fs, loc="upper center", ncol=2)


def industry(axes):
    d = IND[IND["industry_group"] != "Not stated"].copy(); d = d.sort_values("share_value_pct"); y = np.arange(len(d)); h = 0.38; ax = axes[0]
    ax.barh(y + h / 2, d["share_value_pct"], height=h * 0.92, color=BLUE, label="share of total valuation"); ax.barh(y - h / 2, d["share_n_pct"], height=h * 0.92, color=GRAY, label="share of companies")
    ax.set_yticks(y); ax.set_yticklabels([short(s) for s in d["industry_group"]], fontsize=8.5); ax.set_xlabel("% of today's list"); ax.grid(axis="y", visible=False); ax.legend(frameon=False, labelcolor=INK, fontsize=8.5, loc="lower right")
    ax.set_title("Where the value sits (valuation lower bound)", fontsize=12)
    ax = axes[1]; g = GROW[GROW["industry_group"] != "Not stated"].sort_values("n_change_since_2021"); y = np.arange(len(g))
    ax.barh(y, g["n_change_since_2021"], height=0.7, color=[GREEN if v >= 0 else ORANGE for v in g["n_change_since_2021"]])
    for yi, v in zip(y, g["n_change_since_2021"]):
        ax.text(v + (0.8 if v >= 0 else -0.8), yi, f"{v:+d}", va="center", ha="left" if v >= 0 else "right", fontsize=8.5, color=INK)
    ax.axvline(0, color=DIM, linewidth=0.9); ax.set_yticks(y); ax.set_yticklabels([short(s) for s in g["industry_group"]], fontsize=8.5); ax.set_xlim(-18, 42); ax.grid(axis="y", visible=False)
    ax.set_xlabel("companies on the list: Oct 2026 minus Dec 2021"); ax.set_title("Which industries grew on the list", fontsize=12)


def concentration(axes):
    ax = axes[0]; x = np.arange(len(TOPN)); w = 0.27
    for dx, s in zip((-w, 0, w), SNAPS):
        r = CON[CON["snapshot"] == s].iloc[0]; ax.bar(x + dx, [r[c] for c in TOPS], width=w * 0.92, color=SNAPCOL[s], label=s)
    r = CON[CON["snapshot"] == "2026-10-02"].iloc[0]
    for xi, c in zip(x + w, TOPS):
        ax.text(xi, r[c] + 1.5, f"{r[c]:.0f}", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(x); ax.set_xticklabels([f"top {n}" for n in TOPN], fontsize=9); ax.set_ylim(0, 100); ax.grid(axis="x", visible=False); ax.set_ylabel("% of the list's total valuation")
    ax.legend(frameon=False, labelcolor=INK, fontsize=8.5, loc="upper left"); ax.set_title("Top-N share, three snapshots", fontsize=12)
    ax = axes[1]; d = CTY.iloc[::-1].reset_index(drop=True); y = np.arange(len(d)); h = 0.38
    ax.barh(y + h / 2, d["share_value_pct"], height=h * 0.92, color=BLUE, label="share of valuation"); ax.barh(y - h / 2, d["share_n_pct"], height=h * 0.92, color=GRAY, label="share of companies")
    ax.set_yticks(y); ax.set_yticklabels(d["country"], fontsize=9); ax.set_xlabel("% of today's list (first-listed country)"); ax.grid(axis="y", visible=False); ax.legend(frameon=False, labelcolor=INK, fontsize=8.5, loc="lower right"); ax.set_title("Country, by first-listed", fontsize=12)


def stale(axes):
    ax = axes[0]; d = VIN
    ax.bar(d["val_year"], d["n"] - d["n_floor"], color=BLUE, width=0.75, label="exact valuation"); ax.bar(d["val_year"], d["n_floor"], bottom=d["n"] - d["n_floor"], color=GRAY, width=0.75, label='only a floor ("1+", "5+")')
    for yv, n in zip(d["val_year"], d["n"]):
        if n >= 29:
            ax.text(yv, n + 4, str(n), ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(d["val_year"]); ax.set_xticklabels([f"'{str(y)[2:]}" for y in d["val_year"]], fontsize=9); ax.set_ylabel("companies"); ax.grid(axis="x", visible=False); ax.legend(frameon=False, labelcolor=INK, fontsize=8.5, loc="upper left")
    ax.set_xlabel("year of the last valuation"); ax.set_title("When the list's valuations were last set", fontsize=12)
    stale_bars(axes[1]); axes[1].set_title("Old marks are many, but small", fontsize=12)


def age(axes):
    ax = axes[0]; d = AGEH; ax.bar(range(len(d)), d["n"], color=BLUE, width=0.75)
    for i, (n, s) in enumerate(zip(d["n"], d["share_pct"])):
        ax.text(i, n + 1.5, f"{n}", ha="center", fontsize=9, color=INK)
    ax.set_xticks(range(len(d))); ax.set_xticklabels(["0-2", "3-5", "6-8", "9-11", "12-15", "16-30"], fontsize=9); ax.set_xlabel("years from founding to the last listed valuation"); ax.set_ylabel("companies (founding year known)"); ax.grid(axis="x", visible=False)
    ax.set_title(f"{int(d['n'].sum())} of {int(SIZE.iloc[0]['n'])} companies have a founding year", fontsize=12)
    ax = axes[1]; g = AGE.iloc[::-1].reset_index(drop=True); y = np.arange(len(g)); ax.barh(y, g["median_age"], color=BLUE, height=0.7)
    for yi, m, n in zip(y, g["median_age"], g["n_with_age"]):
        ax.text(m + 0.2, yi, f"{m:g}  (n={n})", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y); ax.set_yticklabels([short(s) for s in g["industry_group"]], fontsize=8.5); ax.set_xlim(0, 13); ax.grid(axis="y", visible=False); ax.set_xlabel("median years, founding to last listed valuation"); ax.set_title("By industry group (8+ companies)", fontsize=12)


def survivors(axes):
    ax = axes[0]; cats = [("1: Still listed", GREEN, "still listed"), ("2: Former - Listed (IPO, SPAC, direct)", BLUE, "former: listed"), ("2: Former - Acquired or merged", "#7fb2ee", "former: acquired"),
                          ("2: Former - Failed or written down", ORANGE, "former: failed"), ("2: Former - Reason not stated", "#c9a227", "former: no reason"), ("3: Gone from both tables", GRAY, "gone, no record")]
    for yi, s in enumerate(SNAPS[:2][::-1]):
        left = 0
        for k, c, lab in cats:
            v = SUR[(SUR["snapshot"] == s) & (SUR["status"] == k)]["share_n_pct"]
            v = float(v.iloc[0]) if len(v) else 0.0
            ax.barh(yi, v, left=left, color=c, height=0.55, label=lab if yi == 0 else None)
            if v >= 3:
                ax.text(left + v / 2, yi, f"{v:.0f}%", ha="center", va="center", fontsize=9, color=BG if c in (GREEN, "#7fb2ee", GRAY) else INK)
            left += v
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Dec 2023 list\n(671)", "Dec 2021 list\n(595)"], fontsize=9); ax.set_xlim(0, 100); ax.set_xlabel("where those companies are in Oct 2026 (% of companies)"); ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, labelcolor=INK, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3); ax.set_title("What happened to the older lists", fontsize=12)
    ax = axes[1]; d = EXIT[EXIT["exit_class"].isin(["Listed (IPO, SPAC, direct)", "Acquired or merged", "Failed or written down"])].copy()
    d["same"] = d["n_both"] - d["n_exit_below"] - d["n_exit_above"]; lab = {"Listed (IPO, SPAC, direct)": "listed", "Acquired or merged": "acquired", "Failed or written down": "failed"}; x = np.arange(len(d)); w = 0.38
    ax.bar(x - w / 2, d["n_exit_above"], width=w * 0.92, color=GREEN, label="exit above last valuation"); ax.bar(x + w / 2, d["n_exit_below"], width=w * 0.92, color=ORANGE, label="exit below last valuation")
    for xi, v in list(zip(x - w / 2, d["n_exit_above"])) + list(zip(x + w / 2, d["n_exit_below"])):
        ax.text(xi, v + 1.5, str(int(v)), ha="center", fontsize=9, color=INK)
    ax.set_xticks(x); ax.set_xticklabels([f"{lab[c]}\n(median x{m:.2f})" for c, m in zip(d["exit_class"], d["median_exit_over_last"])], fontsize=9); ax.set_ylabel("former unicorns with both numbers"); ax.grid(axis="x", visible=False)
    ax.set_ylim(0, 118); ax.legend(frameon=False, labelcolor=INK, fontsize=8.5, loc="upper left"); ax.set_title("Exits against the last private valuation", fontsize=12)


def main():
    (HERE / "charts").mkdir(exist_ok=True)
    top5, now = CON[CON["snapshot"] == "2026-10-02"].iloc[0]["top5_pct"], STS.iloc[0]
    fig = plt.figure(figsize=(14, 8)); g = fig.add_gridspec(1, 2, width_ratios=[1, 1]); a = fig.add_subplot(g[0]); b = fig.add_subplot(g[1])
    top_curve(a, fs=10); a.set_title("Share of total valuation held by the N largest companies", fontsize=14)
    stale_bars(b, fs=10); b.set_title("Age of each valuation: companies vs value", fontsize=14)
    fig.suptitle(f"Five companies hold {top5:.0f}% of the list's valuation; {now['stale_pct']:.0f}% of its valuations are 3+ years old", x=0.01, ha="left", fontsize=20, color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(HERE / "charts" / "00_cover.png", dpi=100); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3)); industry(axes); save(fig, "01_industry.png")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9)); concentration(axes); save(fig, "02_concentration.png")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8)); stale(axes); save(fig, "03_stale.png")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9)); age(axes); save(fig, "04_age.png")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2)); survivors(axes); save(fig, "05_survivors.png")


if __name__ == "__main__":
    main()
