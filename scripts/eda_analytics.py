import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import pandas as pd

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
    DATA / "clean_fund_master.csv",
    parse_dates=["launch_date"]
)

nav = pd.read_csv(
    DATA / "clean_nav_history.csv",
    parse_dates=["date"]
)

performance = pd.read_csv(
    DATA / "clean_scheme_performance.csv"
)

transactions = pd.read_csv(
    DATA / "clean_investor_transactions.csv",
    parse_dates=["transaction_date"]
)

portfolio = pd.read_csv(
    DATA / "clean_portfolio_holdings.csv",
    parse_dates=["portfolio_date"]
)

aum = pd.read_csv(
    DATA / "clean_aum_by_fund_house.csv",
    parse_dates=["date"]
)

sip = pd.read_csv(
    DATA / "clean_monthly_sip_inflows.csv"
)

category = pd.read_csv(
    DATA / "clean_category_inflows.csv"
)

folio = pd.read_csv(
    DATA / "clean_industry_folio_count.csv"
)

benchmark = pd.read_csv(
    DATA / "clean_benchmark_indices.csv",
    parse_dates=["date"]
)

print("\nDatasets Loaded Successfully!\n")

datasets = {
    "Fund Master": fund,
    "NAV History": nav,
    "Performance": performance,
    "Transactions": transactions,
    "Portfolio": portfolio,
    "AUM": aum,
    "SIP": sip,
    "Category": category,
    "Folio": folio,
    "Benchmark": benchmark
}

# ----------------------------------------------------------
# Dataset Overview
# ----------------------------------------------------------

print("=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

for name, df in datasets.items():

    print(f"\n{name}")

    print("-" * 35)

    print("Rows :", df.shape[0])
    print("Columns :", df.shape[1])

# ----------------------------------------------------------
# Missing Values
# ----------------------------------------------------------

print("\n")
print("=" * 70)
print("MISSING VALUES")
print("=" * 70)

for name, df in datasets.items():

    missing = df.isnull().sum()

    missing = missing[missing > 0]

    print(f"\n{name}")

    if len(missing) == 0:

        print("No Missing Values")

    else:

        print(missing)

# ----------------------------------------------------------
# Duplicate Rows
# ----------------------------------------------------------

print("\n")
print("=" * 70)
print("DUPLICATE RECORDS")
print("=" * 70)

for name, df in datasets.items():

    duplicates = df.duplicated().sum()

    print(f"{name:<25} {duplicates}")

# ----------------------------------------------------------
# Numerical Statistics
# ----------------------------------------------------------

print("\n")
print("=" * 70)
print("NUMERICAL SUMMARY")
print("=" * 70)

for name, df in datasets.items():

    numeric = df.select_dtypes(include=np.number)

    if numeric.empty:
        continue

    print(f"\n{name}")

    print(numeric.describe())

# ----------------------------------------------------------
# Categorical Statistics
# ----------------------------------------------------------

print("\n")
print("=" * 70)
print("CATEGORICAL SUMMARY")
print("=" * 70)

for name, df in datasets.items():

    categorical = df.select_dtypes(include="object")

    if categorical.empty:
        continue

    print(f"\n{name}")

    print(categorical.describe())

# ==========================================================
# CHART 1 : Fund House Distribution
# ==========================================================

plt.figure(figsize=(12,6))

fund["fund_house"].value_counts().plot(
    kind="bar",
    color="steelblue"
)

plt.title("Number of Mutual Fund Schemes by Fund House")
plt.xlabel("Fund House")
plt.ylabel("Number of Schemes")
plt.xticks(rotation=45)

save_plot("01_fund_house_distribution.png")
plt.close()

# ==========================================================
# CHART 2 : Category Distribution
# ==========================================================

plt.figure(figsize=(8,6))

sns.countplot(
    data=fund,
    x="category",
    order=fund["category"].value_counts().index
)

plt.title("Fund Category Distribution")
plt.xlabel("Category")
plt.ylabel("Count")

save_plot("02_category_distribution.png")
plt.close()

# ==========================================================
# CHART 3 : Sub Category Distribution
# ==========================================================

plt.figure(figsize=(12,6))

fund["sub_category"].value_counts().plot(
    kind="barh",
    color="orange"
)

plt.title("Scheme Sub Categories")
plt.xlabel("Number of Funds")

save_plot("03_subcategory_distribution.png")
plt.close()

# ==========================================================
# CHART 4 : Risk Category Distribution
# ==========================================================

plt.figure(figsize=(9,6))

sns.countplot(
    data=fund,
    y="risk_category",
    order=fund["risk_category"].value_counts().index
)

plt.title("Risk Category Distribution")

save_plot("04_risk_distribution.png")
plt.close()

# ==========================================================
# CHART 5 : Expense Ratio Distribution
# ==========================================================

plt.figure(figsize=(10,6))

sns.histplot(
    performance["expense_ratio_pct"],
    bins=15,
    kde=True,
    color="green"
)

plt.title("Expense Ratio Distribution")
plt.xlabel("Expense Ratio (%)")

save_plot("05_expense_ratio_distribution.png")
plt.close()

# ==========================================================
# CHART 6 : Sharpe Ratio Distribution
# ==========================================================

plt.figure(figsize=(10,6))

sns.histplot(
    performance["sharpe_ratio"],
    bins=20,
    kde=True,
    color="purple"
)

plt.title("Sharpe Ratio Distribution")
plt.xlabel("Sharpe Ratio")

save_plot("06_sharpe_ratio_distribution.png")
plt.close()

# ==========================================================
# CHART 7 : Top 10 Funds by 5-Year Return
# ==========================================================

top10 = (
    performance
    .sort_values("return_5yr_pct", ascending=False)
    .head(10)
)

plt.figure(figsize=(12,7))

sns.barplot(
    data=top10,
    x="return_5yr_pct",
    y="scheme_name",
    palette="viridis"
)

plt.title("Top 10 Funds by 5-Year Return")
plt.xlabel("5-Year Return (%)")
plt.ylabel("Scheme")

save_plot("07_top10_5year_returns.png")
plt.close()

# ==========================================================
# CHART 8 : Return vs Risk
# ==========================================================

plt.figure(figsize=(10,7))

sns.scatterplot(
    data=performance,
    x="std_dev_ann_pct",
    y="return_5yr_pct",
    hue="sharpe_ratio",
    size="aum_crore",
    palette="viridis",
    sizes=(50,400)
)

plt.title("Risk vs Return")
plt.xlabel("Annual Volatility (%)")
plt.ylabel("5-Year Return (%)")

save_plot("08_risk_vs_return.png")
plt.close()

print("="*70)
print("Charts 1-8 Completed")
print("="*70)
# ==========================================================
# CHART 9 : Average NAV Trend
# ==========================================================

nav_trend = (
    nav.groupby("date")["nav"]
    .mean()
    .reset_index()
)

plt.figure(figsize=(13,6))

plt.plot(
    nav_trend["date"],
    nav_trend["nav"],
    linewidth=2
)

plt.title("Average Daily NAV Trend")
plt.xlabel("Date")
plt.ylabel("Average NAV")

save_plot("09_average_nav_trend.png")
plt.close()

# ==========================================================
# CHART 10 : Monthly SIP Inflow Trend
# ==========================================================

plt.figure(figsize=(13,6))

plt.plot(
    sip["month"],
    sip["sip_inflow_crore"],
    marker="o",
    linewidth=2
)

plt.xticks(rotation=45)

plt.title("Monthly SIP Inflows")
plt.xlabel("Month")
plt.ylabel("SIP Inflow (Crore)")

save_plot("10_monthly_sip_trend.png")
plt.close()

# ==========================================================
# CHART 11 : Category-wise Net Inflows
# ==========================================================

category_summary = (
    category
    .groupby("category")["net_inflow_crore"]
    .sum()
    .sort_values(ascending=False)
)

plt.figure(figsize=(12,6))

category_summary.plot(
    kind="bar",
    color="teal"
)

plt.title("Net Inflows by Category")
plt.xlabel("Category")
plt.ylabel("Net Inflow (Crore)")
plt.xticks(rotation=45)

save_plot("11_category_inflows.png")
plt.close()

# ==========================================================
# CHART 12 : Transaction Type Distribution
# ==========================================================

plt.figure(figsize=(8,8))

transactions["transaction_type"].value_counts().plot(
    kind="pie",
    autopct="%1.1f%%",
    startangle=90
)

plt.ylabel("")
plt.title("Transaction Type Distribution")

save_plot("12_transaction_distribution.png")
plt.close()

# ==========================================================
# CHART 13 : Portfolio Sector Allocation
# ==========================================================

sector = (
    portfolio.groupby("sector")["weight_pct"]
    .sum()
    .sort_values(ascending=False)
)

plt.figure(figsize=(12,6))

sector.plot(
    kind="bar",
    color="coral"
)

plt.title("Portfolio Allocation by Sector")
plt.xlabel("Sector")
plt.ylabel("Total Weight (%)")
plt.xticks(rotation=45)

save_plot("13_sector_allocation.png")
plt.close()

# ==========================================================
# CHART 14 : Benchmark Index Trend
# ==========================================================

benchmark_plot = benchmark.copy()

pivot = benchmark_plot.pivot_table(
    index="date",
    columns="index_name",
    values="close_value"
)

plt.figure(figsize=(14,7))

for col in pivot.columns:
    plt.plot(
        pivot.index,
        pivot[col],
        label=col,
        linewidth=2
    )

plt.legend()
plt.title("Benchmark Index Performance")
plt.xlabel("Date")
plt.ylabel("Index Value")

save_plot("14_benchmark_trend.png")
plt.close()

# ==========================================================
# CHART 15 : Correlation Heatmap
# ==========================================================

numeric = performance.select_dtypes(include=np.number).drop(columns=["amfi_code"], errors="ignore")

corr = numeric.corr()

plt.figure(figsize=(12,10))

sns.heatmap(
    corr,
    annot=True,
    cmap="RdYlBu",
    fmt=".2f",
    square=True
)

plt.title("Correlation Heatmap")

save_plot("15_correlation_heatmap.png")
plt.close()

# ==========================================================
# BUSINESS SUMMARY
# ==========================================================

print("\n" + "=" * 70)
print("EDA SUMMARY")
print("=" * 70)

print(f"Total Funds               : {len(fund)}")
print(f"Fund Houses              : {fund['fund_house'].nunique()}")
print(f"Categories               : {fund['category'].nunique()}")
print(f"Sub Categories           : {fund['sub_category'].nunique()}")

print(f"\nAverage Expense Ratio    : {performance['expense_ratio_pct'].mean():.2f}%")
print(f"Average Sharpe Ratio     : {performance['sharpe_ratio'].mean():.2f}")
print(f"Average Beta             : {performance['beta'].mean():.2f}")
print(f"Average Alpha            : {performance['alpha'].mean():.2f}")

print(f"\nHighest Return           : {performance['return_5yr_pct'].max():.2f}%")
print(f"Lowest Return            : {performance['return_5yr_pct'].min():.2f}%")

print("\nEDA Completed Successfully")
print("=" * 70)