-- Ranking de anúncios de influ em agosto/2026, por id_advertising (anúncio único).
WITH b AS (
  SELECT
    id_advertising,
    ANY_VALUE(nm_ad_name)       AS ad_name,
    ANY_VALUE(nm_campaign_name) AS campanha,
    ROUND(SUM(COALESCE(vl_amount_spent,0)),2)   AS spend,
    ROUND(SUM(COALESCE(vl_total_revenue,0)),2)  AS receita,
    SUM(COALESCE(qt_total_sales,0))             AS vendas,
    SUM(COALESCE(qt_impressions,0))             AS impressoes,
    COUNT(DISTINCT reference_date)              AS dias_no_ar
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-08-01' AND '2026-08-31'
    AND (REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')), r'influ|inlfu')
      OR REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')),
         r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni'))
  GROUP BY id_advertising
)
SELECT id_advertising, ad_name, campanha, spend, receita, vendas, impressoes, dias_no_ar,
       ROUND(SAFE_DIVIDE(receita, NULLIF(spend,0)),2) AS retorno
FROM b
ORDER BY receita DESC
