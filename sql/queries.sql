-- Bluestock Fintech Mutual Fund Analytics Platform
-- 10 analytical SQL queries

-- 1. Top 5 funds by AUM (latest performance snapshot)
SELECT scheme_name, fund_house, aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month for a given fund (e.g. SBI Bluechip Regular, 119551)
SELECT strftime('%Y-%m', nav_date) AS month, ROUND(AVG(nav), 2) AS avg_nav
FROM fact_nav
WHERE amfi_code = '119551'
GROUP BY month
ORDER BY month;

-- 3. SIP inflow YoY growth trend (most recent 12 months with data)
SELECT month, sip_inflow_crore, yoy_growth_pct
FROM fact_sip_industry
WHERE yoy_growth_pct IS NOT NULL
ORDER BY month DESC
LIMIT 12;

-- 4. Total transaction amount by state
SELECT state, ROUND(SUM(amount_inr) / 1e7, 2) AS total_amount_crore, COUNT(*) AS num_transactions
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_crore DESC;

-- 5. Funds with expense ratio below 1%
SELECT scheme_name, fund_house, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- 6. Top 5 funds by Sharpe ratio (best risk-adjusted return)
SELECT scheme_name, fund_house, sharpe_ratio, return_3yr_pct
FROM fact_performance
ORDER BY sharpe_ratio DESC
LIMIT 5;

-- 7. SIP vs Lumpsum vs Redemption split (count and total value)
SELECT transaction_type,
       COUNT(*) AS num_transactions,
       ROUND(SUM(amount_inr) / 1e7, 2) AS total_amount_crore
FROM fact_transactions
GROUP BY transaction_type;

-- 8. Average SIP amount by age group
SELECT age_group, ROUND(AVG(amount_inr), 0) AS avg_sip_amount_inr, COUNT(*) AS num_sips
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group
ORDER BY avg_sip_amount_inr DESC;

-- 9. Quarterly AUM growth for the top 3 fund houses (latest quarter)
SELECT fund_house, aum_date, aum_lakh_crore
FROM fact_aum
WHERE aum_date = (SELECT MAX(aum_date) FROM fact_aum)
ORDER BY aum_lakh_crore DESC
LIMIT 3;

-- 10. Sector concentration: top sectors by total portfolio weight across all funds
SELECT sector, ROUND(SUM(weight_pct), 2) AS total_weight_pct, COUNT(DISTINCT amfi_code) AS num_funds_holding
FROM fact_portfolio
GROUP BY sector
ORDER BY total_weight_pct DESC;
