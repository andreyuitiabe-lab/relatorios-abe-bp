-- Portfólio diário de Meta Ads VENDA (agregado)
-- Uso: base para curva de resposta portfólio × dia
-- Filtro: só campanhas de VENDA (exclui LEAD, TESTE, etc.)
-- Output: /dados/midia_paga/daily_spend_venda.csv

SELECT
  reference_date,
  ROUND(SUM(vl_amount_spent), 0)          AS daily_spend,
  SUM(qt_total_sales)                     AS daily_sales,
  ROUND(SUM(vl_total_revenue), 0)         AS daily_revenue,
  ROUND(SAFE_DIVIDE(SUM(vl_total_revenue), SUM(vl_amount_spent)), 2) AS daily_roas,
  ROUND(SAFE_DIVIDE(SUM(vl_amount_spent), SUM(qt_total_sales)), 2)   AS daily_cpa,
  COUNT(DISTINCT nm_campaign_name)        AS qt_campaigns
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE reference_date >= '2026-01-01'
  AND UPPER(nm_campaign_name) LIKE '%VENDA%'
  AND vl_amount_spent > 0
GROUP BY 1
ORDER BY 1
