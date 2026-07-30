Bluestock MF Analytics — Mutual Fund Analytics Platform

A capstone data engineering and analytics project built for Bluestock Fintech, covering end-to-end ETL, a SQLite star-schema database, from-scratch performance and risk metrics, and a 4-page interactive Power BI dashboard

Overview

This project ingests 10 real, AMFI-anchored datasets (40 mutual fund schemes, ~46,000 daily NAV records, ~32,800 investor transactions, spanning Jan 2022 – May 2026), cleans and validates them through an automated Python pipeline, loads them into a normalised SQLite database, computes Sharpe/Sortino/Alpha/Beta/Max Drawdown/VaR metrics independently from raw NAV data, and presents everything through an interactive Power BI dashboard.

bluestock_mf_capstone/

├── data/

│   ├── raw/            # Original 10 provided CSVs

│   ├── processed/      # Cleaned CSVs, computed_performance_metrics.csv, fund_scorecard.csv

│   └── db/             # bluestock_mf.db (SQLite database)

├── notebooks/

│   ├── 03_eda_analysis.ipynb          # 15-chart exploratory data analysis

│   └── 04_performance_analytics.ipynb # Risk/return metrics, fund scorecard

├── scripts/

│   ├── etl_pipeline.py         # Cleans and validates all 10 raw datasets

│   ├── load_db.py              # Loads cleaned data into SQLite

│   ├── eda_analytics.py        # Standalone EDA script (15 charts)

│   ├── performance_analytics.py # Standalone metrics script (6 more charts + scorecard)

│   └── compute_metrics.py      # Core metrics computation module

├── sql/

│   ├── schema.sql      # Star schema DDL (9 tables)

│   └── queries.sql     # 10 analytical SQL queries

├── dashboard/

│   ├── Mutual_Funds_Analytics.pbix  # Power BI dashboard (4 pages)

├── reports/

│   ├── Bluestock_MF_Final_Report.docx

│   ├── Bluestock_MF_Presentation.pptx

│   └── figures/         # All generated chart PNGs

└── data_dictionary.md    # Full column-level documentation of every table

How to Run
1. Install dependencies

bash
pip install pandas numpy matplotlib seaborn scipy --break-system-packages

2. Run the ETL pipeline

bash
python scripts/etl_pipeline.py

This cleans all 10 raw datasets and writes them to data/processed/.

3. Load into SQLite

bash
python scripts/load_db.py

This creates data/db/bluestock_mf.db with the full 9-table star schema.

4. Run the analytics scripts

bash
python scripts/eda_analytics.py
python scripts/performance_analytics.py

These generate 21 charts (in reports/figures/), computed_performance_metrics.csv, and fund_scorecard.csv.

5. Open the dashboard

Open dashboard/Mutual_Funds_Analytics.pbix in Power BI Desktop.

Key Findings
Top-ranked fund by composite scorecard: ICICI Pru Midcap Fund (Regular - Growth), score 85.3/100, with a 31.48% CAGR and 1.18 Sharpe ratio.
Data limitation identified: independently computed Beta values diverged from the pre-supplied scheme_performance.csv, tracing back to the raw NAV and benchmark series not being generated with realistic covariance to each other. Documented in full in the Final Report, Section 7.
SIP inflows hit an all-time high of Rs. 31,002 crore in December 2025, consistent with real published AMFI figures.
Tech Stack

Python 3.10+ (Pandas, NumPy, SciPy, Matplotlib, Seaborn) · SQLite3 · VS Code · Power BI Desktop · Git

Author

Prachi- Data Analyst Intern Bluestock Fintech

Disclaimer

All data is sourced from publicly available AMFI India, mfapi.in, and NSE/BSE information. This project is for educational purposes only and does not constitute financial advice.
