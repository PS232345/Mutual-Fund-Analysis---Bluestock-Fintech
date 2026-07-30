-- Bluestock Fintech Mutual Fund Analytics Platform
-- Star Schema DDL for SQLite

DROP TABLE IF EXISTS dim_fund;
CREATE TABLE dim_fund (
    amfi_code           TEXT PRIMARY KEY,
    fund_house          TEXT,
    scheme_name         TEXT,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      REAL,
    min_lumpsum_amount  REAL,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

DROP TABLE IF EXISTS fact_nav;
CREATE TABLE fact_nav (
    amfi_code           TEXT,
    nav_date            DATE,
    nav                 REAL,
    daily_return_pct    REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
CREATE INDEX idx_fact_nav_code_date ON fact_nav(amfi_code, nav_date);

DROP TABLE IF EXISTS fact_transactions;
CREATE TABLE fact_transactions (
    investor_id         TEXT,
    transaction_date    DATE,
    amfi_code           TEXT,
    transaction_type    TEXT,
    amount_inr          REAL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
CREATE INDEX idx_fact_tx_code_date ON fact_transactions(amfi_code, transaction_date);

DROP TABLE IF EXISTS fact_performance;
CREATE TABLE fact_performance (
    amfi_code           TEXT,
    scheme_name         TEXT,
    fund_house          TEXT,
    category             TEXT,
    plan                TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           REAL,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
CREATE INDEX idx_fact_perf_code ON fact_performance(amfi_code);

DROP TABLE IF EXISTS fact_aum;
CREATE TABLE fact_aum (
    aum_date            DATE,
    fund_house          TEXT,
    aum_lakh_crore      REAL,
    aum_crore           REAL,
    num_schemes         INTEGER
);
CREATE INDEX idx_fact_aum_house_date ON fact_aum(fund_house, aum_date);

DROP TABLE IF EXISTS fact_sip_industry;
CREATE TABLE fact_sip_industry (
    month                       TEXT,
    sip_inflow_crore            REAL,
    active_sip_accounts_crore   REAL,
    new_sip_accounts_lakh       REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL
);

DROP TABLE IF EXISTS fact_category_inflows;
CREATE TABLE fact_category_inflows (
    month           TEXT,
    category        TEXT,
    net_inflow_crore REAL
);

DROP TABLE IF EXISTS fact_folio_count;
CREATE TABLE fact_folio_count (
    month                   TEXT,
    total_folios_crore      REAL,
    equity_folios_crore     REAL,
    debt_folios_crore       REAL,
    hybrid_folios_crore     REAL,
    others_folios_crore     REAL
);

DROP TABLE IF EXISTS fact_portfolio;
CREATE TABLE fact_portfolio (
    amfi_code           TEXT,
    stock_symbol        TEXT,
    stock_name          TEXT,
    sector              TEXT,
    weight_pct          REAL,
    market_value_cr     REAL,
    current_price_inr   REAL,
    portfolio_date      DATE,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
CREATE INDEX idx_fact_portfolio_code ON fact_portfolio(amfi_code);

DROP TABLE IF EXISTS fact_benchmark;
CREATE TABLE fact_benchmark (
    bench_date      DATE,
    index_name      TEXT,
    close_value     REAL
);
CREATE INDEX idx_fact_benchmark_name_date ON fact_benchmark(index_name, bench_date);
