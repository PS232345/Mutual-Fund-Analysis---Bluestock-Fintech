import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(f"[ETL] {msg}")


def clean_fund_master():
    df = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    df["fund_house"] = df["fund_house"].str.strip()
    df["scheme_name"] = df["scheme_name"].str.strip()
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    df = df.drop_duplicates(subset="amfi_code")
    assert df["amfi_code"].is_unique, "Duplicate amfi_code in fund_master!"
    df.to_csv(PROCESSED_DIR / "clean_fund_master.csv", index=False)
    log(f"fund_master: {len(df)} rows cleaned -> clean_fund_master.csv")
    return df


def clean_nav_history(valid_codes):
    df = pd.read_csv(RAW_DIR / "02_nav_history.csv", parse_dates=["date"])
    df = df[df["amfi_code"].isin(valid_codes)]
    df = df.sort_values(["amfi_code", "date"])
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    df = df[df["nav"] > 0]

    # Reindex each fund to a full business-day calendar and forward-fill
    # any missing NAV values (holidays, data gaps).
    filled = []
    for code, grp in df.groupby("amfi_code"):
        full_range = pd.bdate_range(grp["date"].min(), grp["date"].max())
        grp = grp.set_index("date").reindex(full_range)
        grp["amfi_code"] = code
        grp["nav"] = grp["nav"].ffill()
        grp.index.name = "date"
        filled.append(grp.reset_index())
    df = pd.concat(filled, ignore_index=True)

    # Derived field: daily return
    df = df.sort_values(["amfi_code", "date"])
    df["daily_return_pct"] = df.groupby("amfi_code")["nav"].pct_change() * 100

    df.to_csv(PROCESSED_DIR / "clean_nav_history.csv", index=False)
    log(f"nav_history: {len(df)} rows cleaned -> clean_nav_history.csv")
    return df


def clean_aum_by_fund_house():
    df = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv", parse_dates=["date"])
    df["fund_house"] = df["fund_house"].str.strip()
    df = df.drop_duplicates(subset=["date", "fund_house"])
    df.to_csv(PROCESSED_DIR / "clean_aum_by_fund_house.csv", index=False)
    log(f"aum_by_fund_house: {len(df)} rows cleaned -> clean_aum_by_fund_house.csv")
    return df


def clean_monthly_sip_inflows():
    df = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")
    # yoy_growth_pct is legitimately null for the first 12 months (no prior-year base)
    df["yoy_growth_pct"] = df["yoy_growth_pct"].astype("float")
    df.to_csv(PROCESSED_DIR / "clean_monthly_sip_inflows.csv", index=False)
    log(f"monthly_sip_inflows: {len(df)} rows cleaned "
        f"({df['yoy_growth_pct'].isnull().sum()} nulls in yoy_growth_pct expected for year 1)")
    return df


def clean_category_inflows():
    df = pd.read_csv(RAW_DIR / "05_category_inflows.csv")
    df["category"] = df["category"].str.strip()
    df.to_csv(PROCESSED_DIR / "clean_category_inflows.csv", index=False)
    log(f"category_inflows: {len(df)} rows cleaned -> clean_category_inflows.csv")
    return df


def clean_industry_folio_count():
    df = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv")
    df.to_csv(PROCESSED_DIR / "clean_industry_folio_count.csv", index=False)
    log(f"industry_folio_count: {len(df)} rows cleaned -> clean_industry_folio_count.csv")
    return df


def clean_scheme_performance(valid_codes):
    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    df = df[df["amfi_code"].isin(valid_codes)]
    numeric_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
                     "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
                     "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
                     "expense_ratio_pct"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # Flag out-of-range expense ratios per common-mistakes checklist (0.1%-2.5%)
    bad_expense = df[(df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)]
    if len(bad_expense):
        log(f"  WARNING: {len(bad_expense)} funds with expense_ratio outside 0.1-2.5% range")
    df.to_csv(PROCESSED_DIR / "clean_scheme_performance.csv", index=False)
    log(f"scheme_performance: {len(df)} rows cleaned -> clean_scheme_performance.csv")
    return df


def clean_investor_transactions(valid_codes):
    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv", parse_dates=["transaction_date"])
    df["transaction_type"] = df["transaction_type"].str.strip().str.title()
    df = df[df["transaction_type"].isin(["Sip", "Lumpsum", "Redemption"])] if False else df
    df["transaction_type"] = df["transaction_type"].replace({"Sip": "SIP"})
    df = df[df["amount_inr"] > 0]
    df = df[df["amfi_code"].isin(valid_codes)]
    df = df.drop_duplicates()
    df.to_csv(PROCESSED_DIR / "clean_investor_transactions.csv", index=False)
    log(f"investor_transactions: {len(df)} rows cleaned -> clean_investor_transactions.csv")
    return df


def clean_portfolio_holdings(valid_codes):
    df = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv", parse_dates=["portfolio_date"])
    df = df[df["amfi_code"].isin(valid_codes)]
    df["stock_symbol"] = df["stock_symbol"].str.strip().str.upper()
    df = df[df["weight_pct"] > 0]
    df.to_csv(PROCESSED_DIR / "clean_portfolio_holdings.csv", index=False)
    log(f"portfolio_holdings: {len(df)} rows cleaned -> clean_portfolio_holdings.csv")
    return df


def clean_benchmark_indices():
    df = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv", parse_dates=["date"])
    df = df.sort_values(["index_name", "date"])
    df = df.drop_duplicates(subset=["index_name", "date"])
    df = df[df["close_value"] > 0]
    df.to_csv(PROCESSED_DIR / "clean_benchmark_indices.csv", index=False)
    log(f"benchmark_indices: {len(df)} rows cleaned -> clean_benchmark_indices.csv")
    return df


def main():
    log("Starting Bluestock MF ETL pipeline...")
    fund_master = clean_fund_master()
    valid_codes = set(fund_master["amfi_code"])

    clean_nav_history(valid_codes)
    clean_aum_by_fund_house()
    clean_monthly_sip_inflows()
    clean_category_inflows()
    clean_industry_folio_count()
    clean_scheme_performance(valid_codes)
    clean_investor_transactions(valid_codes)
    clean_portfolio_holdings(valid_codes)
    clean_benchmark_indices()

    log("ETL pipeline complete. All cleaned files written to data/processed/")


if __name__ == "__main__":
    main()