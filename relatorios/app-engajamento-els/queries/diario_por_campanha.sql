-- App Engajamento ELS Junho — diário por campanha
-- Tabela: dtm_analytics_google_ads_funnel
-- Métricas: spend, impressões, cliques (qt_outbound_clicks = proxy de re-engajamento)
-- Nota: qt_total_sales e vl_total_revenue são zero por design — campanhas de engajamento não têm atribuição de venda
SELECT
  nm_campaign_name,
  reference_date,
  ROUND(SUM(vl_amount_spent), 2)   AS spend,
  SUM(qt_impressions)              AS impressions,
  SUM(qt_outbound_clicks)          AS clicks,
  ROUND(SAFE_DIVIDE(SUM(qt_outbound_clicks), SUM(qt_impressions)) * 100, 4) AS ctr_pct,
  ROUND(SAFE_DIVIDE(SUM(vl_amount_spent), SUM(qt_outbound_clicks)), 2)      AS cpc,
  ROUND(SAFE_DIVIDE(SUM(vl_amount_spent), SUM(qt_impressions)) * 1000, 2)   AS cpm
FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
WHERE nm_campaign_name IN (
  '[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | Android v2',
  '[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | Android v3',
  '[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | ios'
)
GROUP BY 1, 2
ORDER BY 2, 1
