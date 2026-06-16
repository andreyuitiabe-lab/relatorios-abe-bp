-- Conversão Vitalício por faixa de maturidade na BPDay 2025 (referência jun/jul).
-- Alimenta as taxas de conversão base do Motor 1 para campanhas de verão (jun/jul).
-- Validado em 15/jun/2026.
-- Resultado: 0-3m 0,27% | 3-6m 0,24% | 6-9m 0,59% | 9-12m 0,67%
--            12-18m 1,06% | 18-24m 0,95% | 24m+ 1,50%
WITH
base_ativa_jun2025 AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_type='paid'
    AND dt_started_at <= DATETIME('2025-06-22')
    AND dt_expires_in >= DATETIME('2025-06-22')
),
primeira_compra AS (
  SELECT id_gateway_customer, MIN(dt_ordered_at) AS dt_pc
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status='approved' GROUP BY 1
),
compradores_bpday AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE bl_lifetime_offer=TRUE AND nm_status='approved'
    AND DATE(dt_ordered_at) BETWEEN '2025-06-22' AND '2025-07-31'
)
SELECT faixa, COUNT(*) AS base, COUNTIF(comprou) AS compradores,
  ROUND(COUNTIF(comprou)/COUNT(*)*100,2) AS conv_pct
FROM (
  SELECT
    CASE
      WHEN m BETWEEN 0 AND 2 THEN '0-3m' WHEN m BETWEEN 3 AND 5 THEN '3-6m'
      WHEN m BETWEEN 6 AND 8 THEN '6-9m' WHEN m BETWEEN 9 AND 11 THEN '9-12m'
      WHEN m BETWEEN 12 AND 17 THEN '12-18m' WHEN m BETWEEN 18 AND 23 THEN '18-24m'
      ELSE '24m+' END AS faixa,
    b.id_gateway_customer IN (SELECT id_gateway_customer FROM compradores_bpday) AS comprou
  FROM (
    SELECT ba.id_gateway_customer,
      DATE_DIFF(DATE('2025-06-22'), DATE(p.dt_pc), MONTH) AS m
    FROM base_ativa_jun2025 ba JOIN primeira_compra p USING(id_gateway_customer)
  ) b
)
GROUP BY 1
ORDER BY MIN(CASE faixa WHEN '0-3m' THEN 0 WHEN '3-6m' THEN 3 WHEN '6-9m' THEN 6
  WHEN '9-12m' THEN 9 WHEN '12-18m' THEN 12 WHEN '18-24m' THEN 18 ELSE 24 END);
