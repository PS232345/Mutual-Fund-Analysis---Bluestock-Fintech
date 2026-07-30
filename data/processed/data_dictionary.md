# Bluestock MF Analytics — Data Dictionary

Database: `data/db/bluestock_mf.db` (SQLite)
Source CSVs: `data/raw/` (original) → `data/processed/` (cleaned)

## dim_fund (40 rows)
Master list of mutual fund schemes.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (PK) | Unique AMFI scheme code |
| fund_house | TEXT | AMC name |
| scheme_name | TEXT | Full scheme name |
| category | TEXT | Equity / Debt / Hybrid |
| sub_category | TEXT | Large Cap / Mid Cap / Small Cap / Liquid etc. |
| plan | TEXT | Regular or Direct |
| launch_date | DATE | Fund launch date |
| benchmark | TEXT | Official benchmark index |
| expense_ratio_pct | REAL | Annual expense ratio (%) |
| exit_load_pct | REAL | Exit load (%) |
| min_sip_amount | REAL | Minimum SIP investment (INR) |
| min_lumpsum_amount | REAL | Minimum lumpsum investment (INR) |
| fund_manager | TEXT | Primary fund manager |
| risk_category | TEXT | SEBI risk category |
| sebi_category_code | TEXT | Internal SEBI code |

## fact_nav (46,000 rows)
Daily NAV history per fund, 2022–2026.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (FK) | Links to dim_fund |
| nav_date | DATE | NAV date (business days) |
| nav | REAL | NAV in INR |
| daily_return_pct | REAL | Day-over-day % change (derived) |

## fact_transactions (32,778 rows)
Individual investor transactions.

| Column | Type | Description |
|---|---|---|
| investor_id | TEXT | Unique investor ID |
| transaction_date | DATE | Transaction date |
| amfi_code | TEXT (FK) | Fund invested in |
| transaction_type | TEXT | SIP / Lumpsum / Redemption |
| amount_inr | REAL | Transaction amount (INR) |
| state | TEXT | Investor's state |
| city | TEXT | Investor's city |
| city_tier | TEXT | T30 / B30 (AMFI city classification) |
| age_group | TEXT | Age bracket |
| gender | TEXT | Male / Female |
| annual_income_lakh | REAL | Annual income (INR lakh) |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque |
| kyc_status | TEXT | Verified / Pending |

## fact_performance (40 rows)
Pre-computed performance & risk metrics per scheme.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (FK) | Links to dim_fund |
| return_1yr_pct / return_3yr_pct / return_5yr_pct | REAL | Returns over each period |
| benchmark_3yr_pct | REAL | Benchmark 3yr CAGR |
| alpha | REAL | Excess return over benchmark |
| beta | REAL | Market sensitivity |
| sharpe_ratio | REAL | Risk-adjusted return |
| sortino_ratio | REAL | Downside-risk-adjusted return |
| std_dev_ann_pct | REAL | Annualised volatility |
| max_drawdown_pct | REAL | Worst peak-to-trough decline |
| aum_crore | REAL | Scheme-level AUM |
| morningstar_rating | INTEGER | 1–5 star rating |
| risk_grade | TEXT | Risk classification |

## fact_aum (90 rows)
Quarterly AUM by fund house, 2022–2025.

| Column | Type | Description |
|---|---|---|
| aum_date | DATE | Quarter-end date |
| fund_house | TEXT | AMC name |
| aum_lakh_crore | REAL | Total AUM (INR lakh crore) |
| aum_crore | REAL | Total AUM (INR crore) |
| num_schemes | INTEGER | Number of schemes offered |

## fact_sip_industry (48 rows)
Industry-wide monthly SIP statistics.

| Column | Type | Description |
|---|---|---|
| month | TEXT | YYYY-MM |
| sip_inflow_crore | REAL | Total SIP inflow (INR crore) |
| active_sip_accounts_crore | REAL | Active SIP accounts (crore) |
| new_sip_accounts_lakh | REAL | New registrations that month (lakh) |
| sip_aum_lakh_crore | REAL | Total SIP AUM (INR lakh crore) |
| yoy_growth_pct | REAL | YoY inflow growth % (null for first 12 months — no prior-year base) |

## fact_category_inflows (144 rows)
Monthly net inflows by fund category.

| Column | Type | Description |
|---|---|---|
| month | TEXT | YYYY-MM |
| category | TEXT | Large Cap / Mid Cap / Small Cap / ELSS / Liquid etc. |
| net_inflow_crore | REAL | Net inflow (INR crore) |

## fact_folio_count (21 rows)
Industry-wide investor folio counts over time.

| Column | Type | Description |
|---|---|---|
| month | TEXT | YYYY-MM |
| total_folios_crore | REAL | Total folios (crore) |
| equity_folios_crore / debt_folios_crore / hybrid_folios_crore / others_folios_crore | REAL | Split by category |

## fact_portfolio (322 rows)
Equity fund stock holdings as of Dec 2025.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (FK) | Fund holding the stock |
| stock_symbol | TEXT | NSE/BSE ticker |
| stock_name | TEXT | Company name |
| sector | TEXT | Sector classification |
| weight_pct | REAL | % weight in portfolio |
| market_value_cr | REAL | Holding value (INR crore) |
| current_price_inr | REAL | Stock price |
| portfolio_date | DATE | As-of date |

## fact_benchmark (8,050 rows)
Daily closing values for market benchmark indices.

| Column | Type | Description |
|---|---|---|
| bench_date | DATE | Trading date |
| index_name | TEXT | NIFTY50 / NIFTY100 / NIFTY Midcap 150 / BSE SmallCap / CRISIL Liquid / CRISIL Gilt |
| close_value | REAL | Index closing value |

## Data Quality Notes
- All 40 `amfi_code` values are consistent across every table (no orphan keys).
- No missing NAV dates found beyond weekends (forward-fill logic included in ETL defensively).
- `yoy_growth_pct` is null for the first 12 months of `fact_sip_industry` by design (no prior-year comparison exists) — not a data error.
- All categorical fields (transaction_type, kyc_status, payment_mode, age_group, city_tier) validated against expected value sets.
- Expense ratios validated within the expected 0.1%–2.5% range.
