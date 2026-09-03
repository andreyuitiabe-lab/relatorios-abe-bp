-- Ads Meta com criativo de influenciador: ago/2026 e meses de comparacao
WITH base AS (
  SELECT
    reference_date,
    FORMAT_DATE('%Y-%m', reference_date) AS mes,
    nm_ad_name AS ad_name,
    LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name, NFD), r'\pM','')) AS ad_norm,
    nm_campaign_name AS campanha,
    COALESCE(vl_amount_spent,0)   AS spend,
    COALESCE(vl_total_revenue,0)  AS rev_total,
    COALESCE(vl_direct_revenue,0) AS rev_direct,
    COALESCE(qt_impressions,0)    AS impr,
    COALESCE(qt_total_sales,0)    AS vendas
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-05-01' AND '2026-08-31'
)
SELECT mes, ad_name, ANY_VALUE(campanha) AS campanha,
       ROUND(SUM(spend),2) AS spend,
       ROUND(SUM(rev_total),2) AS rev_total,
       ROUND(SUM(rev_direct),2) AS rev_direct,
       SUM(impr) AS impressoes, SUM(vendas) AS vendas
FROM base
WHERE REGEXP_CONTAINS(ad_norm, r'influ|inlfu')
   OR REGEXP_CONTAINS(ad_norm, r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni')
GROUP BY mes, ad_name
ORDER BY mes, spend DESC
