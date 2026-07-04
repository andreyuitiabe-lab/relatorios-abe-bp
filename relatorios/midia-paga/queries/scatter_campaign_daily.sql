-- Campanha × dia (só VENDA)
-- Uso: base para curva individual por campanha e curva acumulada
-- Output: /dados/midia_paga/scatter_campaign_daily.csv

SELECT
  nm_campaign_name,
  reference_date,
  ROUND(SUM(vl_amount_spent), 0)   AS daily_spend,
  SUM(qt_total_sales)              AS daily_sales,
  ROUND(SUM(vl_total_revenue), 0)  AS daily_revenue
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE reference_date >= '2026-01-01'
  AND UPPER(nm_campaign_name) LIKE '%VENDA%'
  AND vl_amount_spent > 0
GROUP BY 1, 2
ORDER BY 1, 2
