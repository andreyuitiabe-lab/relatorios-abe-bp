-- Vitalício: upgrades entre tiers
-- Identifica clientes que compraram vitalício e depois compraram tier superior
-- Calcula tempo médio até upgrade e incremental gerado

WITH

compras_vitalicio AS (
  SELECT
    t.id_gateway_customer,
    t.dt_ordered_at,
    t.nm_gateway_plan,
    t.vl_payment_gross,
    CASE
      WHEN LOWER(t.nm_gateway_plan) LIKE '%black%'            THEN 4
      WHEN LOWER(t.nm_gateway_plan) LIKE '%premium%'
        OR LOWER(t.nm_gateway_plan) LIKE '%gbb%'              THEN 3
      WHEN LOWER(t.nm_gateway_plan) LIKE '%intermediario%'
        OR LOWER(t.nm_gateway_plan) LIKE '%intermediário%'    THEN 2
      ELSE 1
    END AS nivel_tier
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND (
      LOWER(t.nm_plan_label) LIKE '%vitalício%'
      OR LOWER(t.nm_plan_label) LIKE '%vitalicio%'
    )
),

com_upgrade AS (
  SELECT
    a.id_gateway_customer,
    a.nm_gateway_plan                     AS plano_origem,
    b.nm_gateway_plan                     AS plano_destino,
    a.nivel_tier                          AS nivel_origem,
    b.nivel_tier                          AS nivel_destino,
    a.dt_ordered_at                       AS dt_compra_original,
    b.dt_ordered_at                       AS dt_upgrade,
    DATE_DIFF(b.dt_ordered_at, a.dt_ordered_at, DAY) AS dias_ate_upgrade,
    b.vl_payment_gross                    AS vl_upgrade
  FROM compras_vitalicio a
  JOIN compras_vitalicio b
    ON b.id_gateway_customer = a.id_gateway_customer
    AND b.nivel_tier > a.nivel_tier
    AND b.dt_ordered_at > a.dt_ordered_at
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY a.id_gateway_customer, a.nm_gateway_plan
    ORDER BY b.dt_ordered_at
  ) = 1
)

SELECT
  CONCAT(
    UPPER(SUBSTR(plano_origem, 1, 1)),
    SUBSTR(plano_origem, 2)
  )                                         AS de,
  CONCAT(
    UPPER(SUBSTR(plano_destino, 1, 1)),
    SUBSTR(plano_destino, 2)
  )                                         AS para,
  COUNT(*)                                   AS volume,
  ROUND(AVG(dias_ate_upgrade))               AS dias_medios_ate_upgrade,
  ROUND(SUM(vl_upgrade))                     AS receita_incremental
FROM com_upgrade
GROUP BY de, para
ORDER BY receita_incremental DESC
