-- ============================================================================
-- 00c — Diagnóstico: catálogo completo de ofertas que tocam "mecenas".
-- Usar quando 00a não bater com o briefing: mostra exatamente o que entra e o
-- que sai da definição canônica (coluna `entra_na_definicao`).
-- ============================================================================

SELECT
  nm_gateway_plan,
  nm_gateway_product,
  nm_gateway_offer,
  CASE
    WHEN LOWER(COALESCE(nm_gateway_offer, '')) LIKE '%order bump mecenas%'
      THEN 'NAO - order bump BP Essencial'
    WHEN LOWER(COALESCE(nm_gateway_product, '')) LIKE '%mecenas order bump%'
      THEN 'SIM - tier B0 (upsell R$180)'
    WHEN nm_gateway_plan = 'mecenas_bp-essencial'
      THEN 'NAO - plano bp-essencial'
    WHEN nm_gateway_plan LIKE 'mecenas%'
      OR LOWER(COALESCE(nm_gateway_product, '')) LIKE '%mecenas%'
      THEN 'SIM - bolsa'
    ELSE 'NAO - so a oferta cita mecenas'
  END                                                  AS entra_na_definicao,
  COUNT(*)                                             AS tx,
  COUNT(DISTINCT id_gateway_customer)                  AS clientes,
  ROUND(MIN(vl_payment_gross))                         AS vmin,
  ROUND(APPROX_QUANTILES(vl_payment_gross, 2)[OFFSET(1)]) AS vmediana,
  ROUND(MAX(vl_payment_gross))                         AS vmax,
  ROUND(SUM(vl_payment_gross))                         AS receita,
  COUNTIF(bl_is_commercial_channel)                    AS tx_comercial,
  MIN(DATE(dt_ordered_at))                             AS dt_min,
  MAX(DATE(dt_ordered_at))                             AS dt_max
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status = 'approved'
  AND (   nm_gateway_plan LIKE 'mecenas%'
       OR LOWER(COALESCE(nm_gateway_product, '')) LIKE '%mecenas%'
       OR LOWER(COALESCE(nm_gateway_offer,   '')) LIKE '%mecenas%')
GROUP BY 1, 2, 3, 4
ORDER BY tx DESC
