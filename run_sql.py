"""Steps 2-4: load the parsed Wikipedia tables into DuckDB, run sql/00_setup.sql (views only), then every other sql/*.sql file, writing each result to results/<file name>.csv.

    ./venv/bin/python run_sql.py
"""
from pathlib import Path

import duckdb

HERE = Path(__file__).parent


def main():
    con = duckdb.connect()                                    # in memory: the tables are tiny
    for name, f in [("listed", "parsed/listed.csv"), ("former", "parsed/former.csv"), ("founding", "parsed/founding.csv"), ("wiki_countries", "parsed/wiki_countries.csv"),
                    ("wiki_history", "parsed/wiki_history.csv"), ("industry_rules", "industry_rules.csv")]:
        # all_varchar: a column that is empty in every row must not turn into a number type; the setup casts what it needs
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv('{HERE / f}', header = true, all_varchar = true, nullstr = '<<none>>')")
    for f in sorted((HERE / "sql").glob("*.sql")):
        if f.name.startswith("00_"):
            con.execute(f.read_text())                         # setup: views, nothing to export
            continue
        out = HERE / "results" / f"{f.stem}.csv"
        con.execute(f.read_text()).fetchdf().to_csv(out, index=False)
        print(f"{f.name:28s} -> {out.name}")


if __name__ == "__main__":
    main()
