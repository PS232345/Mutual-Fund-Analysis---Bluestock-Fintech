import sqlite3
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE / "data" / "processed"
DB_PATH = BASE / "data" / "db" / "bluestock_mf.db"
SCHEMA_PATH = BASE / "sql" / "schema.sql"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Apply schema
    with open(SCHEMA_PATH) as f:
        cur.executescript(f.read())
    conn.commit()
    print(f"[DB] Schema applied to {DB_PATH}")

    # --- dim_fund ---
    df = pd.read_csv(PROCESSED_DIR / "clean_fund_master.csv")
    df.to_sql("dim_fund", conn, if_exists="append", index=False)
    print(f"[DB] dim_fund: {len(df)} rows loaded")

    # --- fact_nav ---
    df = pd.read_csv(PROCESSED_DIR / "clean_nav_history.csv")
    df = df.rename(columns={"date": "nav_date"})[["amfi_code", "nav_date", "nav", "daily_return_pct"]]
    df.to_sql("fact_nav", conn, if_exists="append", index=False)
    print(f"[DB] fact_nav: {len(df)} rows loaded")

    # --- fact_transactions ---
    df = pd.read_csv(PROCESSED_DIR / "clean_investor_transactions.csv")
    df.to_sql("fact_transactions", conn, if_exists="append", index=False)
    print(f"[DB] fact_transactions: {len(df)} rows loaded")

    # --- fact_performance ---
    df = pd.read_csv(PROCESSED_DIR / "clean_scheme_performance.csv")
    df.to_sql("fact_performance", conn, if_exists="append", index=False)
    print(f"[DB] fact_performance: {len(df)} rows loaded")

    # --- fact_aum ---
    df = pd.read_csv(PROCESSED_DIR / "clean_aum_by_fund_house.csv")
    df = df.rename(columns={"date": "aum_date"})
    df.to_sql("fact_aum", conn, if_exists="append", index=False)
    print(f"[DB] fact_aum: {len(df)} rows loaded")

    # --- fact_sip_industry ---
    df = pd.read_csv(PROCESSED_DIR / "clean_monthly_sip_inflows.csv")
    df.to_sql("fact_sip_industry", conn, if_exists="append", index=False)
    print(f"[DB] fact_sip_industry: {len(df)} rows loaded")

    # --- fact_category_inflows ---
    df = pd.read_csv(PROCESSED_DIR / "clean_category_inflows.csv")
    df.to_sql("fact_category_inflows", conn, if_exists="append", index=False)
    print(f"[DB] fact_category_inflows: {len(df)} rows loaded")

    # --- fact_folio_count ---
    df = pd.read_csv(PROCESSED_DIR / "clean_industry_folio_count.csv")
    df.to_sql("fact_folio_count", conn, if_exists="append", index=False)
    print(f"[DB] fact_folio_count: {len(df)} rows loaded")

    # --- fact_portfolio ---
    df = pd.read_csv(PROCESSED_DIR / "clean_portfolio_holdings.csv")
    df.to_sql("fact_portfolio", conn, if_exists="append", index=False)
    print(f"[DB] fact_portfolio: {len(df)} rows loaded")

    # --- fact_benchmark ---
    df = pd.read_csv(PROCESSED_DIR / "clean_benchmark_indices.csv")
    df = df.rename(columns={"date": "bench_date"})
    df.to_sql("fact_benchmark", conn, if_exists="append", index=False)
    print(f"[DB] fact_benchmark: {len(df)} rows loaded")

    conn.commit()
    conn.close()
    print(f"[DB] All tables loaded successfully into {DB_PATH}")


if __name__ == "__main__":
    main()