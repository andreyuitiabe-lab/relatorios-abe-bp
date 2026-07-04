-- Métricas do funil por dia (portfólio VENDA agregado)
-- Uso: análise de hook rate, CTR, CPM, correlação com CPA
-- Output: /tmp/funnel_daily.csv (uso ad-hoc)

SELECT
  reference_date,
  ROUND(SUM(vl_amount_spent), 0)                     AS spend,
  SUM(qt_impressions)                                AS impressions,
  SUM(qt_outbound_clicks)                            AS clicks,
  SUM(qt_three_second_views)                         AS view3s,
  SUM(qt_thruplays)                                  AS thruplays,
  SUM(qt_total_sales)                                AS sales,
  ROUND(SUM(vl_total_revenue), 0)                    AS revenue
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE reference_date >= '2026-01-01'
  AND UPPER(nm_campaign_name) LIKE '%VENDA%'
  AND vl_amount_spent > 0
GROUP BY 1
ORDER BY 1
