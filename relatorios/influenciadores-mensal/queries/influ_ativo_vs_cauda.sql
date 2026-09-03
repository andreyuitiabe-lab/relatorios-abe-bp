-- Separa, por influenciador, a receita das peças que RODARAM em agosto
-- da receita de peças pausadas (cauda de meses anteriores).
WITH b AS (
  SELECT id_advertising, ANY_VALUE(nm_ad_name) ad,
         SUM(COALESCE(vl_amount_spent,0))  s,
         SUM(COALESCE(vl_total_revenue,0)) r,
         SUM(COALESCE(qt_total_sales,0))   v,
         SUM(COALESCE(qt_impressions,0))   impr,
         COUNTIF(COALESCE(qt_impressions,0) > 0) dias_com_impressao
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-08-01' AND '2026-08-31'
    AND (REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')), r'influ|inlfu')
      OR REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')),
         r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni'))
  GROUP BY 1
)
SELECT
  CASE
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'murillo capellozzi') THEN 'Murillo Capellozzi'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'josue aragao')       THEN 'Josué Aragão'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'alam carri')         THEN 'Alam Carrion'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'diego del rio')      THEN 'Diego Del Rio'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'fran otto')          THEN 'Fran Otto'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'br ?explora')        THEN 'BR Explora'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'pedro alaer')        THEN 'Pedro Alaer'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'arthur schreiber')   THEN 'Arthur Schreiber'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'julliene salviano')  THEN 'Julliene Salviano'
    WHEN REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(ad,NFD),r'\pM','')), r'mayara ranni')       THEN 'Mayara Ranni'
    ELSE 'demais' END AS influ,
  ROUND(SUM(s),0)                 AS gasto,
  ROUND(SUM(IF(s>=1, r, 0)),0)    AS receita_ativa,
  ROUND(SUM(IF(s<1,  r, 0)),0)    AS receita_cauda,
  ROUND(SAFE_DIVIDE(SUM(IF(s>=1,r,0)), SUM(s)),2) AS retorno_ativo,
  ROUND(SAFE_DIVIDE(SUM(r), SUM(s)),2)            AS retorno_caixa
FROM b GROUP BY influ ORDER BY gasto DESC
