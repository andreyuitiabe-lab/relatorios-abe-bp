-- A mesma venda do Comercial é atribuída a vários anúncios de influ?
WITH influ AS (
  SELECT nm_ad_name, arr_commercial_deals_breakdown AS arr,
         COALESCE(vl_commercial_total_revenue,0) com_rev,
         COALESCE(vl_total_revenue,0) tot, COALESCE(vl_direct_revenue,0) dir
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-08-01' AND '2026-08-31'
    AND (REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')), r'influ|inlfu')
      OR REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')),
         r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni'))
), ex AS (
  SELECT s.id_transaction, s.vl_payment_gross
  FROM influ, UNNEST(arr) d, UNNEST(d.arr_sales_transaction_ids) s
)
SELECT
  (SELECT ROUND(SUM(tot),2) FROM influ)     AS vl_total_revenue,
  (SELECT ROUND(SUM(dir),2) FROM influ)     AS vl_direct_revenue,
  (SELECT ROUND(SUM(com_rev),2) FROM influ) AS vl_commercial_revenue,
  COUNT(*)                       AS ocorrencias_comercial,
  COUNT(DISTINCT id_transaction) AS transacoes_comerciais_distintas,
  ROUND(SUM(vl_payment_gross),2) AS soma_com_repeticao,
  (SELECT ROUND(SUM(vl_payment_gross),2) FROM (
     SELECT DISTINCT id_transaction, vl_payment_gross FROM ex)) AS soma_dedup
FROM ex
