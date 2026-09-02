-- Spend diário total de mídia (Meta + Google + PMax), 2025-08-01 →
-- ⚠️ Meta só tem spend desde 2025-08-01 (limite da série)
SELECT
  reference_date AS dia,
  ROUND(SUM(IF(fonte = 'meta', spend, 0))) AS spend_meta,
  ROUND(SUM(IF(fonte != 'meta', spend, 0))) AS spend_google_pmax,
  ROUND(SUM(spend)) AS spend_total
FROM (
  SELECT DATE(reference_date) AS reference_date, vl_amount_spent AS spend, 'meta' AS fonte
  FROM datamart.dtm_analytics_facebook_ads_funnel
  UNION ALL
  SELECT DATE(reference_date), vl_amount_spent, 'google'
  FROM datamart.dtm_analytics_google_ads_funnel
  UNION ALL
  SELECT DATE(reference_date), vl_amount_spent, 'pmax'
  FROM datamart.dtm_analytics_pmax_ads_funnel
)
WHERE reference_date BETWEEN '2025-08-01' AND '2026-08-20'
GROUP BY 1
ORDER BY 1
