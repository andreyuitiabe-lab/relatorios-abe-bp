-- Dentro da receita atribuída aos anúncios de influ:
--   direta   = a pessoa viu o anúncio e comprou sozinha
--   comercial= a pessoa virou lead pelo anúncio e um vendedor fechou depois
WITH b AS (
  SELECT
    LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name, NFD), r'\pM','')) AS ad_norm,
    SUM(COALESCE(vl_amount_spent,0))            AS spend,
    SUM(COALESCE(vl_direct_revenue,0))          AS rec_direta,
    SUM(COALESCE(vl_commercial_total_revenue,0))AS rec_comercial,
    SUM(COALESCE(qt_direct_sales,0))            AS v_diretas,
    SUM(COALESCE(qt_commercial_total_sales,0))  AS v_comerciais
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-08-01' AND '2026-08-31'
    AND (REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')), r'influ|inlfu')
      OR REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')),
         r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni'))
  GROUP BY ad_norm
)
SELECT
  CASE
    WHEN REGEXP_CONTAINS(ad_norm,r'murillo capellozzi') THEN 'Murillo Capellozzi'
    WHEN REGEXP_CONTAINS(ad_norm,r'josue aragao')       THEN 'Josué Aragão'
    WHEN REGEXP_CONTAINS(ad_norm,r'alam carri')         THEN 'Alam Carrion'
    WHEN REGEXP_CONTAINS(ad_norm,r'diego del rio')      THEN 'Diego Del Rio'
    WHEN REGEXP_CONTAINS(ad_norm,r'fran otto')          THEN 'Fran Otto'
    WHEN REGEXP_CONTAINS(ad_norm,r'br ?explora')        THEN 'BR Explora'
    WHEN REGEXP_CONTAINS(ad_norm,r'pedro alaer')        THEN 'Pedro Alaer'
    WHEN REGEXP_CONTAINS(ad_norm,r'arthur schreiber')   THEN 'Arthur Schreiber'
    WHEN REGEXP_CONTAINS(ad_norm,r'julliene salviano')  THEN 'Julliene Salviano'
    WHEN REGEXP_CONTAINS(ad_norm,r'mayara ranni')       THEN 'Mayara Ranni'
    ELSE 'demais' END AS influ,
  ROUND(SUM(spend),0) gasto,
  ROUND(SUM(rec_direta),0) direta, SUM(v_diretas) v_dir,
  ROUND(SUM(rec_comercial),0) comercial, SUM(v_comerciais) v_com,
  ROUND(100*SAFE_DIVIDE(SUM(rec_comercial), SUM(rec_direta)+SUM(rec_comercial)),0) pct_comercial,
  ROUND(SAFE_DIVIDE(SUM(rec_direta), SUM(spend)),2) retorno_so_direta
FROM b GROUP BY influ ORDER BY gasto DESC
