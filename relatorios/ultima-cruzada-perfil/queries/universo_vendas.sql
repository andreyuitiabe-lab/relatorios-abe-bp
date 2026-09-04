-- Universo Coleção Brasil: A Última Cruzada (set/2026) — visão por plano/canal/status
WITH uc AS (
  SELECT *
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE DATE(dt_ordered_at) >= '2026-08-01'
    AND ( nm_gateway_plan LIKE 'colecao-brasil%'
       OR REGEXP_CONTAINS(LOWER(COALESCE(nm_gateway_product,'')), r'cole[cç][aã]o brasil') )
)
SELECT
  nm_gateway_plan,
  CASE WHEN bl_is_commercial_channel THEN 'Comercial' ELSE 'Digital' END canal,
  nm_status,
  COUNT(*) tx,
  COUNT(DISTINCT id_gateway_customer) pessoas,
  ROUND(SUM(vl_payment_gross),0) receita,
  ROUND(AVG(vl_payment_gross),0) ticket
FROM uc
GROUP BY 1,2,3
ORDER BY 1,2,3
