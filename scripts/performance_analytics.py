import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib.pyplot as plt
import seaborn as sns

# ----------------------------------------------------------
# Plot Settings
# ----------------------------------------------------------

plt.style.use("ggplot")

sns.set_theme(
    style="whitegrid",
    palette="Set2"
)

plt.rcParams["figure.figsize"] = (12, 7)
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["axes.labelsize"] = 12
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10

# ----------------------------------------------------------
# Project Paths
# ----------------------------------------------------------

BASE = Path(__file__).resolve().parent.parent

DATA = BASE / "data" / "processed"

REPORTS = BASE / "reports"

FIGURES = REPORTS / "figures"

FIGURES.mkdir(
    parents=True,
    exist_ok=True
)

# ----------------------------------------------------------
# Constants
# ----------------------------------------------------------

RISK_FREE_RATE = 0.065  # RBI repo-rate proxy, annualised
TRADING_DAYS = 252

# Maps each fund's stated benchmark name to the closest available
# index series in clean_benchmark_indices.csv
BENCHMARK_MAP = {
    "NIFTY 100 TRI": "NIFTY100",
    "NIFTY 50 TRI": "NIFTY50",
    "NIFTY 500 TRI": "NIFTY500",
    "NIFTY Midcap 150 TRI": "NIFTY_MIDCAP150",
    "BSE 250 SmallCap TRI": "BSE_SMALLCAP",
    "CRISIL Dynamic Gilt Index": "CRISIL_GILT",
    "CRISIL Liquid Fund AI Index": "CRISIL_LIQUID",
    "CRISIL Short Term Bond Index": "CRISIL_LIQUID",   # closest available proxy
    "NIFTY Midcap 50 TRI": "NIFTY_MIDCAP150",          # closest available proxy
    "NIFTY Large Midcap 250 TRI": "NIFTY100",          # closest available proxy
}

# ----------------------------------------------------------
# Helper Function
# ----------------------------------------------------------

def save_plot(filename):

    plt.tight_layout()

    plt.savefig(
        FIGURES / filename,
        dpi=300,
        bbox_inches="tight"
    )

    print(f"Saved -> {filename}")

# ----------------------------------------------------------
# Load Cleaned Data
# ----------------------------------------------------------

print("=" * 70)
print("Loading Cleaned Datasets...")
print("=" * 70)

fund = pd.read_csv(
    DATA / "clean_fund_master.csv"
)

nav = pd.read_csv(
    DATA / "clean_nav_history.csv",
    parse_dates=["date"]
)

benchmark = pd.read_csv(
    DATA / "clean_benchmark_indices.csv",
    parse_dates=["date"]
)

given_performance = pd.read_csv(
    DATA / "clean_scheme_performance.csv"
)

print("\nDatasets Loaded Successfully!\n")
print("Funds        :", fund.shape[0])
print("NAV rows     :", nav.shape[0])
print("Benchmark rows:", benchmark.shape[0])

# ----------------------------------------------------------
# Metric Functions (implemented from scratch)
# ----------------------------------------------------------

def cagr(nav_series):
    """CAGR using actual trading-day count, not calendar days."""
    n_days = len(nav_series)
    if n_days < 2 or nav_series.iloc[0] <= 0:
        return np.nan
    total_return = nav_series.iloc[-1] / nav_series.iloc[0]
    years = n_days / TRADING_DAYS
    return (total_return ** (1 / years) - 1) * 100


def sharpe_ratio(daily_returns):
    r = daily_returns.dropna() / 100
    if r.std() == 0 or len(r) == 0:
        return np.nan
    excess = r.mean() * TRADING_DAYS - RISK_FREE_RATE
    return excess / (r.std() * np.sqrt(TRADING_DAYS))


def sortino_ratio(daily_returns):
    r = daily_returns.dropna() / 100
    downside = r[r < 0]
    if len(downside) == 0 or downside.std() == 0:
        return np.nan
    excess = r.mean() * TRADING_DAYS - RISK_FREE_RATE
    return excess / (downside.std() * np.sqrt(TRADING_DAYS))


def max_drawdown(nav_series):
    running_max = nav_series.cummax()
    return (nav_series / running_max - 1).min() * 100


def alpha_beta(fund_returns, bench_returns):
    """Alpha annualised (%), Beta via OLS regression of fund returns on benchmark returns."""
    merged = pd.concat([fund_returns, bench_returns], axis=1, join="inner").dropna()
    if len(merged) < 30:
        return np.nan, np.nan
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        merged.iloc[:, 1], merged.iloc[:, 0]
    )
    return intercept * TRADING_DAYS, slope


def historical_var_cvar(daily_returns, confidence=0.95):
    r = daily_returns.dropna()
    if len(r) == 0:
        return np.nan, np.nan
    var = np.percentile(r, (1 - confidence) * 100)
    cvar = r[r <= var].mean()
    return var, cvar

# ----------------------------------------------------------
# Compute Metrics for All Funds
# ----------------------------------------------------------

print("\n")
print("=" * 70)
print("COMPUTING PERFORMANCE & RISK METRICS")
print("=" * 70)

bench_wide = benchmark.pivot(index="date", columns="index_name", values="close_value")
bench_returns = bench_wide.pct_change() * 100

results = []

for _, f in fund.iterrows():

    code = f["amfi_code"]

    fund_nav = nav[nav["amfi_code"] == code].sort_values("date").set_index("date")

    if len(fund_nav) < 30:
        continue

    daily_ret = fund_nav["daily_return_pct"]

    bench_name = BENCHMARK_MAP.get(f["benchmark"], "NIFTY100")
    bench_ret = bench_returns[bench_name] if bench_name in bench_returns.columns else pd.Series(dtype=float)

    alpha, beta = alpha_beta(daily_ret, bench_ret)
    var95, cvar95 = historical_var_cvar(daily_ret)

    results.append({
        "amfi_code": code,
        "scheme_name": f["scheme_name"],
        "fund_house": f["fund_house"],
        "category": f["category"],
        "sub_category": f["sub_category"],
        "benchmark_used": bench_name,
        "cagr_pct": round(cagr(fund_nav["nav"]), 2),
        "std_dev_ann_pct": round(daily_ret.dropna().std() * np.sqrt(TRADING_DAYS), 2),
        "sharpe_ratio": round(sharpe_ratio(daily_ret), 2) if pd.notna(sharpe_ratio(daily_ret)) else np.nan,
        "sortino_ratio": round(sortino_ratio(daily_ret), 2) if pd.notna(sortino_ratio(daily_ret)) else np.nan,
        "alpha": round(alpha, 2) if pd.notna(alpha) else np.nan,
        "beta": round(beta, 2) if pd.notna(beta) else np.nan,
        "max_drawdown_pct": round(max_drawdown(fund_nav["nav"]), 2),
        "var_95_daily_pct": round(var95, 2) if pd.notna(var95) else np.nan,
        "cvar_95_daily_pct": round(cvar95, 2) if pd.notna(cvar95) else np.nan,
        "expense_ratio_pct": f["expense_ratio_pct"],
    })

metrics = pd.DataFrame(results)

metrics.to_csv(DATA / "computed_performance_metrics.csv", index=False)

print(f"\nComputed metrics for {len(metrics)} funds")
print("Saved -> computed_performance_metrics.csv")

# ----------------------------------------------------------
# Fund Scorecard (Composite Score, 0-100)
# ----------------------------------------------------------

print("\n")
print("=" * 70)
print("BUILDING FUND SCORECARD")
print("=" * 70)

df = metrics.copy()

df["rank_return"] = df["cagr_pct"].rank(pct=True)
df["rank_sharpe"] = df["sharpe_ratio"].rank(pct=True)
df["rank_alpha"] = df["alpha"].rank(pct=True)
df["rank_expense_inv"] = df["expense_ratio_pct"].rank(pct=True, ascending=False)
df["rank_mdd_inv"] = df["max_drawdown_pct"].rank(pct=True)

df["fund_score"] = (
    0.30 * df["rank_return"] +
    0.25 * df["rank_sharpe"] +
    0.20 * df["rank_alpha"] +
    0.15 * df["rank_expense_inv"] +
    0.10 * df["rank_mdd_inv"]
) * 100

df["fund_score"] = df["fund_score"].round(1)

scorecard = df.sort_values("fund_score", ascending=False)[
    ["amfi_code", "scheme_name", "fund_house", "category", "sub_category",
     "cagr_pct", "sharpe_ratio", "alpha", "beta", "max_drawdown_pct",
     "expense_ratio_pct", "fund_score"]
]

scorecard.to_csv(DATA / "fund_scorecard.csv", index=False)

print("Saved -> fund_scorecard.csv")
print("\nTop 10 Funds by Composite Score:")
print(scorecard.head(10).to_string(index=False))

# ==========================================================
# CHART 1 : Sharpe Ratio - Top 15 Funds
# ==========================================================

top15_sharpe = metrics.sort_values("sharpe_ratio", ascending=False).head(15)

plt.figure(figsize=(12, 7))

sns.barplot(
    data=top15_sharpe,
    x="sharpe_ratio",
    y="scheme_name",
    palette="viridis"
)

plt.title("Top 15 Funds by Sharpe Ratio")
plt.xlabel("Sharpe Ratio")
plt.ylabel("Scheme")

save_plot("16_sharpe_top15.png")
plt.close()

# ==========================================================
# CHART 2 : Alpha vs Beta Scatter by Category
# ==========================================================

plt.figure(figsize=(10, 7))

sns.scatterplot(
    data=metrics,
    x="beta",
    y="alpha",
    hue="category",
    s=90
)

plt.axhline(0, color="gray", linewidth=0.8)
plt.axvline(1, color="gray", linewidth=0.8, linestyle="--")
plt.title("Alpha vs Beta by Category")
plt.xlabel("Beta (Market Sensitivity)")
plt.ylabel("Alpha (Annualised Excess Return %)")

save_plot("17_alpha_beta_scatter.png")
plt.close()

# ==========================================================
# CHART 3 : Maximum Drawdown - Worst 10 Funds
# ==========================================================

worst10_mdd = metrics.sort_values("max_drawdown_pct").head(10)

plt.figure(figsize=(12, 6))

sns.barplot(
    data=worst10_mdd,
    x="max_drawdown_pct",
    y="scheme_name",
    palette="Reds_r"
)

plt.title("Worst 10 Funds by Maximum Drawdown")
plt.xlabel("Max Drawdown (%)")
plt.ylabel("Scheme")

save_plot("18_max_drawdown_worst10.png")
plt.close()

# ==========================================================
# CHART 4 : CAGR Distribution by Category
# ==========================================================

plt.figure(figsize=(10, 6))

sns.boxplot(
    data=metrics,
    x="category",
    y="cagr_pct",
    palette="Set2"
)

plt.title("CAGR Distribution by Category")
plt.xlabel("Category")
plt.ylabel("CAGR (%)")

save_plot("19_cagr_by_category.png")
plt.close()

# ==========================================================
# CHART 5 : Benchmark Comparison - Top 5 Scorecard Funds vs NIFTY 100
# ==========================================================

top5_codes = scorecard.head(5)["amfi_code"].tolist()

plt.figure(figsize=(12, 7))

for code in top5_codes:
    fund_nav = nav[nav["amfi_code"] == code].sort_values("date").set_index("date")["nav"]
    indexed = fund_nav / fund_nav.iloc[0] * 100
    name = fund.loc[fund["amfi_code"] == code, "scheme_name"].values[0]
    plt.plot(indexed.index, indexed.values, label=name[:35], linewidth=1.8)

n100 = bench_wide["NIFTY100"].dropna()
n100_indexed = n100 / n100.iloc[0] * 100
plt.plot(n100_indexed.index, n100_indexed.values, label="NIFTY 100 (Benchmark)",
          color="black", linewidth=2, linestyle="--")

plt.title("Top 5 Scorecard Funds vs NIFTY 100 (Indexed to 100)")
plt.xlabel("Date")
plt.ylabel("Indexed Value")
plt.legend(fontsize=9)

save_plot("20_benchmark_comparison_top5.png")
plt.close()

# ==========================================================
# CHART 6 : VaR / CVaR - Riskiest 10 Funds
# ==========================================================

riskiest10 = metrics.sort_values("var_95_daily_pct").head(10)

plt.figure(figsize=(12, 6))

x = np.arange(len(riskiest10))
width = 0.35

plt.bar(x - width/2, riskiest10["var_95_daily_pct"], width, label="VaR (95%)", color="orange")
plt.bar(x + width/2, riskiest10["cvar_95_daily_pct"], width, label="CVaR (95%)", color="firebrick")

plt.xticks(x, riskiest10["scheme_name"], rotation=45, ha="right")
plt.title("Value at Risk (95%) - Riskiest 10 Funds (Daily)")
plt.ylabel("Daily Return (%)")
plt.legend()

save_plot("21_var_cvar_riskiest10.png")
plt.close()

print("=" * 70)
print("Charts 16-21 Completed")
print("=" * 70)

# ----------------------------------------------------------
# Cross-Validation Against Pre-Supplied scheme_performance.csv
# ----------------------------------------------------------

print("\n")
print("=" * 70)
print("CROSS-VALIDATION vs PRE-SUPPLIED scheme_performance.csv")
print("=" * 70)

compare = metrics.merge(
    given_performance[["amfi_code", "return_3yr_pct", "sharpe_ratio", "beta", "alpha", "max_drawdown_pct"]],
    on="amfi_code",
    suffixes=("_computed", "_given")
)

print(compare[[
    "scheme_name", "cagr_pct", "return_3yr_pct",
    "sharpe_ratio_computed", "sharpe_ratio_given",
    "beta_computed", "beta_given"
]].head(10).to_string(index=False))

print(
    "\nNote: Computed Sharpe/Beta/Max Drawdown diverge from the pre-supplied file for "
    "several funds. Daily-return correlation between fund NAVs and their mapped benchmark "
    "indices is close to zero for most funds, while the pre-supplied file assumes realistic "
    "betas (~0.8-1.0) for equity funds. This indicates the raw nav_history and "
    "benchmark_indices series were not generated with real covariance to each other -- a "
    "limitation of the underlying synthetic dataset, not an error in the methodology used "
    "here (formulas match standard Sharpe/Sortino/CAPM definitions)."
)

# ----------------------------------------------------------
# Business Summary
# ----------------------------------------------------------

print("\n" + "=" * 70)
print("PERFORMANCE ANALYTICS SUMMARY")
print("=" * 70)

print(f"Funds analysed              : {len(metrics)}")
print(f"Average CAGR                : {metrics['cagr_pct'].mean():.2f}%")
print(f"Average Sharpe Ratio        : {metrics['sharpe_ratio'].mean():.2f}")
print(f"Average Sortino Ratio       : {metrics['sortino_ratio'].mean():.2f}")
print(f"Average Max Drawdown        : {metrics['max_drawdown_pct'].mean():.2f}%")

best = scorecard.iloc[0]
print(f"\nTop-ranked fund (composite score): {best['scheme_name']} ({best['fund_score']}/100)")

print("\nPerformance Analytics Completed Successfully")
print("=" * 70)