-- ============================================================================
-- 00a — SANITY CHECK obrigatório: volume mensal vs. briefing
-- ----------------------------------------------------------------------------
-- Alvo (briefing ago/2026), coluna tx_total deve bater:
--   2026-03: 2.535 tx / R$1,07M / R$421   (campanha de massa)
--   2026-06:    75 tx / R$214k  / R$2.859
--   2026-07:   214 tx / R$785k  / R$3.668  (180 comercial)
--   2026-08:   172 tx / R$288k  / R$1.672  (65 comercial, até 07/08)
-- Se não bater → rodar 00c_ofertas.sql e revisar a exclusão do order bump.
-- ============================================================================

SELECT
  FORMAT_DATE('%Y-%m', DATE(t.dt_ordered_at))       AS mes,
  COUNT(*)                                          AS tx_total,
  COUNTIF(NOT bump.f)                               AS tx_bolsa,
  COUNTIF(bump.f)                                   AS tx_bump_180,
  COUNTIF(t.bl_is_commercial_channel)               AS tx_comercial,
  COUNT(DISTINCT LOWER(c.nm_email))                 AS pessoas,
  ROUND(SUM(t.vl_payment_gross))                    AS receita,
  ROUND(AVG(t.vl_payment_gross))                    AS ticket_medio
FROM `bp-datawarehouse.masterdata.fct_transactions` t
JOIN `bp-datawarehouse.masterdata.dim_contact`      c USING (id_gateway_customer)
CROSS JOIN UNNEST([STRUCT(
  LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas order bump%' AS f
)]) AS bump
WHERE t.nm_status = 'approved'
  AND (
    (t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
    OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%'
  )
  AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump mecenas%'
  AND DATE(t.dt_ordered_at) >= '2025-01-01'
GROUP BY mes
ORDER BY mes
