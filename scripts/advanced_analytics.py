import sqlite3
from pathlib import Path
 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
 
# ------------------------------------------------------------------
# CONFIG — adjust paths to match your project structure
# ------------------------------------------------------------------
DB_PATH = Path("bluestock_mf.db")
OUTPUT_DIR = Path("data/processed")
REPORT_DIR = Path("reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
 
RISK_FREE_RATE = 0.065  # RBI repo rate proxy, annualised
TRADING_DAYS = 252
VAR_CONFIDENCE = 0.95
AT_RISK_GAP_DAYS = 35
 
# Funds to use for the rolling Sharpe chart (edit as needed)
ROLLING_SHARPE_FUNDS = None  # None = auto-pick first 5 amfi_codes found
 
 
def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DB_PATH.resolve()}. "
            "Run this script from your project root, or edit DB_PATH."
        )
    return sqlite3.connect(DB_PATH)
 
 
# ------------------------------------------------------------------
# 1. HISTORICAL VaR + CVaR
# ------------------------------------------------------------------
def compute_var_cvar(conn):
    print("[1/6] Computing Historical VaR / CVaR ...")
    nav = pd.read_sql("SELECT amfi_code, nav_date, nav FROM fact_nav ORDER BY amfi_code, nav_date", conn)
    nav["nav_date"] = pd.to_datetime(nav["nav_date"])
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
 
    results = []
    for code, grp in nav.groupby("amfi_code"):
        returns = grp["daily_return"].dropna()
        if len(returns) < 30:
            continue
        var_95 = np.percentile(returns, (1 - VAR_CONFIDENCE) * 100)
        cvar_95 = returns[returns <= var_95].mean()
        results.append({
            "amfi_code": code,
            "var_95_daily_pct": round(var_95 * 100, 3),
            "cvar_95_daily_pct": round(cvar_95 * 100, 3),
            "var_95_annualised_pct": round(var_95 * np.sqrt(TRADING_DAYS) * 100, 3),
        })
 
    df = pd.DataFrame(results).sort_values("var_95_daily_pct")
    out_path = OUTPUT_DIR / "var_cvar_report.csv"
    df.to_csv(out_path, index=False)
    print(f"    -> saved {out_path} ({len(df)} funds)")
    return df
 
 
# ------------------------------------------------------------------
# 2. ROLLING 90-DAY SHARPE
# ------------------------------------------------------------------
def compute_rolling_sharpe(conn):
    print("[2/6] Computing rolling 90-day Sharpe ratio ...")
    nav = pd.read_sql("SELECT amfi_code, nav_date, nav FROM fact_nav ORDER BY amfi_code, nav_date", conn)
    nav["nav_date"] = pd.to_datetime(nav["nav_date"])
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
 
    daily_rf = RISK_FREE_RATE / TRADING_DAYS
    funds = ROLLING_SHARPE_FUNDS or nav["amfi_code"].unique()[:5]
 
    plt.figure(figsize=(11, 6))
    for code in funds:
        sub = nav[nav["amfi_code"] == code].set_index("nav_date")["daily_return"]
        excess = sub - daily_rf
        rolling_sharpe = (
            excess.rolling(90).mean() / excess.rolling(90).std() * np.sqrt(TRADING_DAYS)
        )
        plt.plot(rolling_sharpe.index, rolling_sharpe.values, label=str(code))
 
    plt.axhline(0, color="grey", linewidth=0.8)
    plt.title("Rolling 90-Day Sharpe Ratio")
    plt.xlabel("Date")
    plt.ylabel("Sharpe Ratio (annualised)")
    plt.legend(title="AMFI Code", fontsize=8)
    plt.tight_layout()
    out_path = REPORT_DIR / "rolling_sharpe_chart.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"    -> saved {out_path}")
 
 
# ------------------------------------------------------------------
# 3. INVESTOR COHORT ANALYSIS
# ------------------------------------------------------------------
def compute_cohort_analysis(conn):
    print("[3/6] Running investor cohort analysis ...")
    tx = pd.read_sql(
        "SELECT investor_id, transaction_date, amfi_code, transaction_type, amount_inr "
        "FROM fact_transactions", conn
    )
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
 
    first_tx = tx.groupby("investor_id")["transaction_date"].min().rename("first_tx_date")
    tx = tx.merge(first_tx, on="investor_id")
    tx["cohort_year"] = tx["first_tx_date"].dt.year
 
    sip = tx[tx["transaction_type"] == "SIP"]
    cohort = (
        sip.groupby("cohort_year")
        .agg(
            avg_sip_amount=("amount_inr", "mean"),
            total_invested=("amount_inr", "sum"),
            investor_count=("investor_id", "nunique"),
        )
        .reset_index()
    )
    top_fund_per_cohort = (
        sip.groupby(["cohort_year", "amfi_code"])["amount_inr"]
        .sum()
        .reset_index()
        .sort_values(["cohort_year", "amount_inr"], ascending=[True, False])
        .groupby("cohort_year")
        .first()
        .rename(columns={"amfi_code": "top_fund_amfi_code"})[["top_fund_amfi_code"]]
        .reset_index()
    )
    cohort = cohort.merge(top_fund_per_cohort, on="cohort_year", how="left")
 
    out_path = OUTPUT_DIR / "cohort_analysis.csv"
    cohort.to_csv(out_path, index=False)
    print(f"    -> saved {out_path}")
    return cohort
 
 
# ------------------------------------------------------------------
# 4. SIP CONTINUATION / AT-RISK FLAGGING
# ------------------------------------------------------------------
def compute_sip_continuity(conn):
    print("[4/6] Checking SIP continuation patterns ...")
    tx = pd.read_sql(
        "SELECT investor_id, transaction_date, transaction_type FROM fact_transactions "
        "WHERE transaction_type = 'SIP'", conn
    )
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
 
    results = []
    for investor_id, grp in tx.groupby("investor_id"):
        dates = grp["transaction_date"].sort_values()
        if len(dates) < 6:
            continue
        gaps = dates.diff().dt.days.dropna()
        avg_gap = gaps.mean()
        max_gap = gaps.max()
        results.append({
            "investor_id": investor_id,
            "sip_count": len(dates),
            "avg_gap_days": round(avg_gap, 1),
            "max_gap_days": int(max_gap),
            "at_risk": max_gap > AT_RISK_GAP_DAYS,
        })
 
    df = pd.DataFrame(results)
    out_path = OUTPUT_DIR / "sip_continuity.csv"
    df.to_csv(out_path, index=False)
    at_risk_pct = df["at_risk"].mean() * 100 if len(df) else 0
    print(f"    -> saved {out_path} ({at_risk_pct:.1f}% of qualifying investors flagged at-risk)")
    return df
 
 
# ------------------------------------------------------------------
# 5. FUND RECOMMENDER
# ------------------------------------------------------------------
def recommend_funds(conn, risk_appetite: str, top_n: int = 3):
    """
    risk_appetite: 'Low' | 'Moderate' | 'High'
    Maps to risk_category in dim_fund, ranks matching funds by Sharpe ratio.
    """
    risk_map = {
        "Low": ["Low", "Moderate"],
        "Moderate": ["Moderate", "High"],
        "High": ["High", "Very High"],
    }
    if risk_appetite not in risk_map:
        raise ValueError("risk_appetite must be one of: Low, Moderate, High")
 
    query = """
        SELECT f.amfi_code, f.scheme_name, f.fund_house, f.risk_category,
               p.sharpe_ratio, p.return_3yr_pct, p.expense_ratio_pct
        FROM dim_fund f
        JOIN fact_performance p ON f.amfi_code = p.amfi_code
        WHERE f.risk_category IN ({})
        ORDER BY p.sharpe_ratio DESC
        LIMIT {}
    """.format(
        ",".join(f"'{r}'" for r in risk_map[risk_appetite]), top_n
    )
    return pd.read_sql(query, conn)
 
 
def demo_recommender(conn):
    print("[5/6] Running fund recommender demo (Low / Moderate / High) ...")
    for appetite in ["Low", "Moderate", "High"]:
        try:
            recs = recommend_funds(conn, appetite)
            print(f"\n    Top picks for '{appetite}' risk appetite:")
            print(recs.to_string(index=False))
        except Exception as e:
            print(f"    Skipped '{appetite}': {e}")
 
 
# ------------------------------------------------------------------
# 6. SECTOR CONCENTRATION (HHI)
# ------------------------------------------------------------------
def compute_sector_hhi(conn):
    print("[6/6] Computing sector concentration (HHI) ...")
    holdings = pd.read_sql(
        "SELECT amfi_code, sector, weight_pct FROM fact_portfolio", conn
    )
    sector_weights = holdings.groupby(["amfi_code", "sector"])["weight_pct"].sum().reset_index()
    hhi = (
        sector_weights.assign(weight_sq=lambda d: d["weight_pct"] ** 2)
        .groupby("amfi_code")["weight_sq"]
        .sum()
        .reset_index()
        .rename(columns={"weight_sq": "hhi"})
    )
    hhi["concentration"] = pd.cut(
        hhi["hhi"], bins=[0, 1500, 2500, 10000],
        labels=["Diversified", "Moderate", "Concentrated"]
    )
 
    out_path = OUTPUT_DIR / "sector_hhi.csv"
    hhi.to_csv(out_path, index=False)
 
    plt.figure(figsize=(9, 5))
    hhi.sort_values("hhi").plot(
        kind="barh", x="amfi_code", y="hhi", legend=False, ax=plt.gca()
    )
    plt.xlabel("HHI (sector concentration)")
    plt.title("Sector Concentration by Fund")
    plt.tight_layout()
    chart_path = REPORT_DIR / "sector_hhi_chart.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()
 
    print(f"    -> saved {out_path} and {chart_path}")
    return hhi
 
 
# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    conn = get_connection()
    try:
        compute_var_cvar(conn)
        compute_rolling_sharpe(conn)
        compute_cohort_analysis(conn)
        compute_sip_continuity(conn)
        demo_recommender(conn)
        compute_sector_hhi(conn)
    finally:
        conn.close()
 
    print("\nDay 6 advanced analytics complete. Outputs in data/processed/ and reports/.")
 
 
if __name__ == "__main__":
    main()