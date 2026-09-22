-- Regra da wiki (meta-insider-ads.md): varrer as 3 tabelas de funil, nao so o Meta.
-- Meta-only subconta a verba do lancamento.
SELECT 'meta' AS canal,
  IF(REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]'), 'LAC', 'ENE') AS sigla,
  ROUND(SUM(vl_amount_spent)) AS vl_spend, SUM(qt_impressions) AS qt_impressoes,
  SUM(qt_total_sales) AS qt_vendas, ROUND(SUM(vl_total_revenue)) AS vl_receita
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') AND reference_date BETWEEN '2026-09-19' AND '2026-09-21')
   OR (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[ene\]') AND reference_date BETWEEN '2026-07-28' AND '2026-07-30')
GROUP BY 1, 2
UNION ALL
SELECT 'pmax',
  IF(REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]'), 'LAC', 'ENE'),
  ROUND(SUM(vl_amount_spent)), SUM(qt_impressions), SUM(qt_total_sales), ROUND(SUM(vl_total_revenue))
FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
WHERE (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') AND reference_date BETWEEN '2026-09-19' AND '2026-09-21')
   OR (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[ene\]') AND reference_date BETWEEN '2026-07-28' AND '2026-07-30')
GROUP BY 1, 2
UNION ALL
SELECT 'google',
  IF(REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]'), 'LAC', 'ENE'),
  ROUND(SUM(vl_amount_spent)), SUM(qt_impressions), SUM(qt_total_sales), ROUND(SUM(vl_total_revenue))
FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
WHERE (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') AND reference_date BETWEEN '2026-09-19' AND '2026-09-21')
   OR (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[ene\]') AND reference_date BETWEEN '2026-07-28' AND '2026-07-30')
GROUP BY 1, 2
ORDER BY sigla, canal
