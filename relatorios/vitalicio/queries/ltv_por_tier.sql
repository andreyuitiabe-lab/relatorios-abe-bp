-- Vitalício: LTV por tier
-- LTV = receita de entrada + todas as transações aprovadas posteriores do mesmo cliente
-- Tier definido pela primeira compra vitalícia (nm_gateway_plan)

WITH

primeira_compra_vitalicia AS (
  SELECT
    t.id_gateway_customer,
    MIN(t.dt_ordered_at)  AS dt_primeira_compra,
    FIRST_VALUE(t.nm_gateway_plan) OVER (
      PARTITION BY t.id_gateway_customer
      ORDER BY t.dt_ordered_at
    )                     AS plano_entrada,
    SUM(t.vl_payment_gross) OVER (
      PARTITION BY t.id_gateway_customer
      ORDER BY t.dt_ordered_at
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                     AS vl_entrada
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND (
      LOWER(t.nm_plan_label) LIKE '%vitalício%'
      OR LOWER(t.nm_plan_label) LIKE '%vitalicio%'
    )
  QUALIFY ROW_NUMBER() OVER (PARTITION BY t.id_gateway_customer ORDER BY t.dt_ordered_at) = 1
),

tier AS (
  SELECT
    id_gateway_customer,
    dt_primeira_compra,
    vl_entrada,
    CASE
      WHEN LOWER(plano_entrada) LIKE '%black%'                THEN 'Black'
      WHEN LOWER(plano_entrada) LIKE '%premium%'
        OR LOWER(plano_entrada) LIKE '%gbb%'                  THEN 'Premium GBB'
      WHEN LOWER(plano_entrada) LIKE '%intermediario%'
        OR LOWER(plano_entrada) LIKE '%intermediário%'         THEN 'Intermediário'
      ELSE 'Básico'
    END AS tier_entrada
  FROM primeira_compra_vitalicia
),

receita_total AS (
  SELECT
    t.id_gateway_customer,
    SUM(t.vl_payment_gross) AS vl_ltv_total
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN tier ti ON ti.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
  GROUP BY 1
)

SELECT
  ti.tier_entrada,
  COUNT(DISTINCT ti.id_gateway_customer)          AS compradores,
  ROUND(SUM(ti.vl_entrada))                       AS receita_entrada,
  ROUND(AVG(ti.vl_entrada))                       AS ticket_medio_entrada,
  ROUND(SUM(rt.vl_ltv_total))                     AS ltv_total,
  ROUND(AVG(rt.vl_ltv_total))                     AS ltv_medio,
  ROUND(
    (SUM(rt.vl_ltv_total) - SUM(ti.vl_entrada))
    / NULLIF(SUM(ti.vl_entrada), 0) * 100, 1
  )                                                AS pct_incremental
FROM tier ti
LEFT JOIN receita_total rt ON rt.id_gateway_customer = ti.id_gateway_customer
GROUP BY ti.tier_entrada
ORDER BY ltv_total DESC
