-- Série diária agregada das campanhas de marca (KW Institucional) — proxy de demanda de marca
SELECT
  DATE(reference_date) AS dia,
  ROUND(SUM(qt_impressions)) AS impressoes_marca,
  ROUND(SUM(qt_outbound_clicks)) AS cliques_marca,
  ROUND(SUM(vl_amount_spent)) AS spend_marca,
  COUNT(DISTINCT nm_campaign_name) AS n_campanhas
FROM datamart.dtm_analytics_google_ads_funnel
WHERE REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[kw\].*institucional')
  AND DATE(reference_date) BETWEEN '2025-08-01' AND '2026-08-20'
GROUP BY 1 ORDER BY 1
