-- Mídia e receita por semana (segunda a domingo) e anúncio, desde {INI}.
SELECT FORMAT_DATE('%Y-%m-%d', DATE_TRUNC(reference_date, WEEK(MONDAY))) semana, CAST(id_advertising AS STRING) ad_id,
  ROUND(SUM(COALESCE(vl_amount_spent,0)),2) gasto, ROUND(SUM(COALESCE(vl_total_revenue,0)),2) receita
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE reference_date >= '{INI}'
GROUP BY 1, 2
