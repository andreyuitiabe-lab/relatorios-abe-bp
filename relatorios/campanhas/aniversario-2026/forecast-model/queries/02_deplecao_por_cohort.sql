-- ANÁLISE DE DEPLEÇÃO POR COHORT — peça central do modelo de forecast.
-- Pergunta: a mesma safra de 1ª compra, exposta à oferta de Vitalício campanha após
-- campanha, se esgota. Quanto cada nova campanha extrai vs a anterior?
-- Validado em 15/jun/2026.

-- 2a) Penetração acumulada de Vitalício DENTRO da base ativa, por cohort anual.
--     Mostra quanto de cada safra já foi "consumido" pela oferta.
--     Resultado: 2020 28,0% | 2021 24,7% | 2022 17,7% | 2023 29,9%
--                2024 11,7% | 2025 2,6% | 2026 0,7%
WITH
membros_ativos AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_status IN ('active','wo renewal') AND nm_type='paid'
    AND dt_started_at <= CURRENT_DATETIME() AND dt_expires_in >= CURRENT_DATETIME()
  UNION DISTINCT
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE bl_lifetime_offer = TRUE AND nm_status='approved'
),
primeira_compra AS (
  SELECT id_gateway_customer, MIN(dt_ordered_at) AS dt_primeira_compra
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status='approved' GROUP BY 1
),
vitalicio AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE bl_lifetime_offer = TRUE AND nm_status='approved'
)
SELECT
  EXTRACT(YEAR FROM p.dt_primeira_compra) AS cohort_ano,
  COUNT(*) AS base_ativa,
  COUNTIF(v.id_gateway_customer IS NOT NULL) AS ja_vitalicio,
  ROUND(COUNTIF(v.id_gateway_customer IS NOT NULL)/COUNT(*)*100,1) AS pct_penetracao
FROM membros_ativos m
JOIN primeira_compra p USING (id_gateway_customer)
LEFT JOIN vitalicio v ON m.id_gateway_customer = v.id_gateway_customer
GROUP BY 1 ORDER BY 1;

-- 2b) FATOR DE DEPLEÇÃO POR CICLO: razão entre Vitalícios extraídos de uma mesma
--     cohort em BF2024 vs BF2023. Mede o decaimento quando a safra repete exposição.
--     Resultado: cohort 2020 → 0,59 | 2021 → 0,59 | 2022 → 0,61
--     >>> FATOR DE DEPLEÇÃO ≈ 0,60 por ciclo de campanha (cohort já trabalhada) <<<
WITH
primeira_compra AS (
  SELECT id_gateway_customer, MIN(dt_ordered_at) AS dt_pc
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status='approved' GROUP BY 1
),
vit AS (
  SELECT DISTINCT t.id_gateway_customer,
    CASE WHEN DATE(t.dt_ordered_at) BETWEEN '2023-11-01' AND '2023-11-30' THEN 'BF2023'
         WHEN DATE(t.dt_ordered_at) BETWEEN '2024-11-01' AND '2024-11-30' THEN 'BF2024' END AS camp
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.bl_lifetime_offer=TRUE AND t.nm_status='approved'
)
SELECT
  EXTRACT(YEAR FROM p.dt_pc) AS cohort,
  COUNTIF(v.camp='BF2023') AS vit_bf23,
  COUNTIF(v.camp='BF2024') AS vit_bf24,
  ROUND(SAFE_DIVIDE(COUNTIF(v.camp='BF2024'), COUNTIF(v.camp='BF2023')),2) AS razao_bf24_bf23
FROM primeira_compra p
LEFT JOIN vit v USING (id_gateway_customer)
WHERE EXTRACT(YEAR FROM p.dt_pc) IN (2020,2021,2022)
GROUP BY 1 ORDER BY 1;

-- 2c) Vitalícios extraídos por campanha x cohort (visão completa da depleção).
--     Confirma que cada campanha vive do pool fresco (cohort mais nova rende mais)
--     e que cohorts antigas decaem campanha a campanha.
WITH
primeira_compra AS (
  SELECT id_gateway_customer, MIN(dt_ordered_at) AS dt_primeira_compra
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status='approved' GROUP BY 1
),
vitalicio_campanha AS (
  SELECT DISTINCT t.id_gateway_customer,
    CASE
      WHEN DATE(t.dt_ordered_at) BETWEEN '2023-11-01' AND '2023-11-30' THEN 'BF2023'
      WHEN DATE(t.dt_ordered_at) BETWEEN '2024-11-01' AND '2024-11-30' THEN 'BF2024'
      WHEN DATE(t.dt_ordered_at) BETWEEN '2025-06-22' AND '2025-07-31' THEN 'BPDay2025'
      WHEN DATE(t.dt_ordered_at) BETWEEN '2025-11-01' AND '2025-11-30' THEN 'BF2025'
    END AS campanha
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.bl_lifetime_offer = TRUE AND t.nm_status='approved'
)
SELECT vc.campanha, EXTRACT(YEAR FROM p.dt_primeira_compra) AS cohort_ano,
  COUNT(DISTINCT vc.id_gateway_customer) AS compradores_vit
FROM vitalicio_campanha vc
JOIN primeira_compra p USING (id_gateway_customer)
WHERE vc.campanha IS NOT NULL
GROUP BY 1,2 ORDER BY 1,2;
