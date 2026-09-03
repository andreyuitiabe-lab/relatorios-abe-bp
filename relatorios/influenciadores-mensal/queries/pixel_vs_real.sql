-- O algoritmo otimiza pelo que o pixel reporta. A BP fatura o que está no fct.
-- Se divergirem, a escala do algoritmo vai para o criativo errado.
WITH b AS (
  SELECT
    LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name, NFD), r'\pM','')) AS ad_norm,
    COALESCE(vl_amount_spent,0)       AS spend,
    COALESCE(qt_fb_pixel_purchases,0) AS pixel_compras,
    COALESCE(qt_total_sales,0)        AS vendas_reais,
    COALESCE(vl_total_revenue,0)      AS receita
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-08-01' AND '2026-08-31'
)
SELECT
  CASE
    WHEN REGEXP_CONTAINS(ad_norm, r'murillo capellozzi') THEN 'Murillo Capellozzi'
    WHEN REGEXP_CONTAINS(ad_norm, r'josue[ _-]?aragao')  THEN 'Josué Aragão'
    WHEN REGEXP_CONTAINS(ad_norm, r'alam carri')         THEN 'Alam Carrion'
    WHEN REGEXP_CONTAINS(ad_norm, r'diego del rio')      THEN 'Diego Del Rio'
    WHEN REGEXP_CONTAINS(ad_norm, r'fran[ _-]?otto')     THEN 'Fran Otto'
    WHEN REGEXP_CONTAINS(ad_norm, r'arthur[ _-]?schreiber') THEN 'Arthur Schreiber'
    WHEN REGEXP_CONTAINS(ad_norm, r'mayara[ _-]?ranni')  THEN 'Mayara Ranni'
    WHEN REGEXP_CONTAINS(ad_norm, r'br ?explora')        THEN 'BR Explora'
    WHEN REGEXP_CONTAINS(ad_norm, r'pedro alaer')        THEN 'Pedro Alaer'
    WHEN REGEXP_CONTAINS(ad_norm, r'julliene salviano')  THEN 'Julliene Salviano'
    ELSE NULL END AS influ,
  ROUND(SUM(spend),0)         AS spend,
  ROUND(SUM(pixel_compras),0) AS pixel_compras,
  SUM(vendas_reais)           AS vendas_reais,
  ROUND(SAFE_DIVIDE(SUM(pixel_compras), SUM(vendas_reais)),2) AS pixel_por_venda_real,
  ROUND(SAFE_DIVIDE(SUM(spend), SUM(pixel_compras)),2)        AS custo_por_compra_pixel,
  ROUND(SAFE_DIVIDE(SUM(receita), SUM(spend)),2)              AS retorno_real
FROM b
WHERE ad_norm IS NOT NULL
GROUP BY influ HAVING influ IS NOT NULL AND spend > 1000
ORDER BY spend DESC
