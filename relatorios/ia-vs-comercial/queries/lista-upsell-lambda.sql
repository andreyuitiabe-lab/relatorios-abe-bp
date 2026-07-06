-- Lista de compradores Lambda sem deal ativo no Pipedrive
-- Uso: identificar oportunidades de upsell para o Comercial abordar
--
-- Critérios de inclusão:
--   - Compra aprovada via Lambda (C0113) nos últimos 90 dias
--   - NÃO é renovação automática
-- Critérios de exclusão:
--   - Cliente já tem deal ABERTO com vendedor humano no Pipedrive

WITH lambda_buyers AS (
  SELECT
    id_gateway_customer,
    MAX(dt_ordered_at)    AS dt_compra,
    MAX(nm_plan_label)    AS produto,
    SUM(vl_payment_gross) AS vl_compra
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status      = 'approved'
    AND bl_is_renovation = FALSE
    AND UPPER(nm_pptc_tracking_name) LIKE '%C0113%'
    AND DATE(dt_ordered_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
  GROUP BY id_gateway_customer
),

em_atendimento AS (
  -- Deal ABERTO com vendedor humano (exclui funil Mecenas que é fluxo separado)
  SELECT DISTINCT dc.id_gateway_customer
  FROM `bp-datawarehouse.datamart.dtm_pipedrive_analytics` pa
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc
    ON dc.nm_email = pa.nm_person_email
  WHERE pa.nm_status   = 'OPEN'
    AND pa.nm_pipeline NOT LIKE '%MECENAS%'
)

SELECT
  dc.nm_name                 AS nome,
  dc.nm_email                AS email,
  dc.cd_cleaned_phone_number AS telefone,
  lb.produto,
  DATE(lb.dt_compra)         AS dt_compra,
  ROUND(lb.vl_compra, 2)     AS vl_compra
FROM lambda_buyers lb
JOIN `bp-datawarehouse.masterdata.dim_contact` dc
  ON dc.id_gateway_customer = lb.id_gateway_customer
LEFT JOIN em_atendimento ea
  ON ea.id_gateway_customer = lb.id_gateway_customer
WHERE ea.id_gateway_customer IS NULL  -- sem deal ativo com vendedor humano
  AND dc.nm_email IS NOT NULL
ORDER BY lb.dt_compra DESC
