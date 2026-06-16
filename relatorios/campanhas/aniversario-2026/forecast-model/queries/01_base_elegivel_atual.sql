-- Base ativa elegível para upsell Vitalício (sem Vitalício ainda) por faixa de maturidade
-- Validado em 15/jun/2026. Alimenta o Motor 1 (upsell) do forecast.
-- Resultado: 0-3m 72.658 | 3-6m 48.818 | 6-9m 52.880 | 9-12m 46.188
--            12-18m 96.645 | 18-24m 59.681 | 24m+ 181.221 | Total ~558.091
WITH
compradores_vitalicio AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE bl_lifetime_offer = TRUE AND nm_status = 'approved'
),
membros_ativos AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_status IN ('active', 'wo renewal')
    AND nm_type = 'paid'
    AND dt_started_at <= CURRENT_DATETIME()
    AND dt_expires_in >= CURRENT_DATETIME()
),
primeira_compra AS (
  SELECT id_gateway_customer, MIN(dt_ordered_at) AS dt_primeira_compra
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
  GROUP BY 1
)
SELECT
  CASE
    WHEN meses < 3 THEN '0-3m' WHEN meses < 6 THEN '3-6m'
    WHEN meses < 9 THEN '6-9m' WHEN meses < 12 THEN '9-12m'
    WHEN meses < 18 THEN '12-18m' WHEN meses < 24 THEN '18-24m'
    ELSE '24m+' END AS faixa,
  COUNT(*) AS elegiveis
FROM (
  SELECT m.id_gateway_customer,
    DATE_DIFF(CURRENT_DATE(), DATE(p.dt_primeira_compra), MONTH) AS meses
  FROM membros_ativos m
  LEFT JOIN primeira_compra p USING (id_gateway_customer)
  WHERE m.id_gateway_customer NOT IN (SELECT id_gateway_customer FROM compradores_vitalicio)
)
GROUP BY 1 ORDER BY MIN(meses);
