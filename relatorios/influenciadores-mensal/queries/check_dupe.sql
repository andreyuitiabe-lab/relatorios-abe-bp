-- A mesma transação aparece em mais de uma linha (ad x dia)?
WITH influ AS (
  SELECT id_advertising, nm_ad_name, arr_st_all_approved_transactions AS arr,
         COALESCE(vl_total_revenue,0) rev, COALESCE(qt_total_sales,0) vendas
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-08-01' AND '2026-08-31'
    AND (REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')), r'influ|inlfu')
      OR REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')),
         r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni'))
), exploded AS (
  SELECT t.id_transaction, t.vl_payment_gross, t.dt_ordered_at
  FROM influ, UNNEST(arr) t
)
SELECT
  (SELECT ROUND(SUM(rev),2) FROM influ)                                  AS soma_vl_total_revenue,
  (SELECT SUM(vendas) FROM influ)                                        AS soma_qt_total_sales,
  COUNT(*)                                                               AS linhas_no_array,
  COUNT(DISTINCT id_transaction)                                         AS transacoes_distintas,
  ROUND(SUM(vl_payment_gross),2)                                         AS receita_somando_array,
  (SELECT ROUND(SUM(vl_payment_gross),2) FROM (
      SELECT DISTINCT id_transaction, vl_payment_gross FROM exploded))    AS receita_dedup
FROM exploded
