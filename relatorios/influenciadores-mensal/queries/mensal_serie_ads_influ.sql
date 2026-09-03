WITH b AS (
  SELECT FORMAT_DATE('%Y-%m', reference_date) AS mes,
    REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name, NFD), r'\pM','')),
      r'influ|inlfu|arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni') AS is_influ,
    COALESCE(vl_amount_spent,0) s, COALESCE(vl_total_revenue,0) rt,
    COALESCE(vl_direct_revenue,0) rd, COALESCE(qt_total_sales,0) v
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-01-01' AND '2026-08-31'
)
SELECT mes,
  ROUND(SUM(IF(is_influ,s,0)),0)  AS spend_influ,
  ROUND(SUM(IF(is_influ,rt,0)),0) AS rec_influ,
  ROUND(SUM(IF(is_influ,rd,0)),0) AS rec_dir_influ,
  SUM(IF(is_influ,v,0))           AS vendas_influ,
  ROUND(SUM(s),0)                 AS spend_total,
  ROUND(SUM(rt),0)                AS rec_total,
  ROUND(SAFE_DIVIDE(SUM(IF(is_influ,rt,0)),SUM(IF(is_influ,s,0))),2) AS roas_influ,
  ROUND(SAFE_DIVIDE(SUM(rt),SUM(s)),2) AS roas_geral,
  ROUND(100*SAFE_DIVIDE(SUM(IF(is_influ,s,0)),SUM(s)),1) AS pct_spend_influ
FROM b GROUP BY mes ORDER BY mes
