-- Desfecho de compra de TODOS os leads da campanha "Conteúdo bloqueado" (Lambda)
-- População: direto da fonte Pipedrive (staging.int_pipedrive_analytics), pelo
-- padrão de título 'UPSELL |%' — mais robusto que nm_label (hoje 100% coincidem;
-- 2.912 deals, todos wellington.santos / '9. OUTROS', criados em lotes desde 20/07/2026).
-- Venda Lambda = link do Gustavo Koetz, C0113 no tracking name (regra canônica na
-- wiki fluxo-comercial.md). Vendas de outros canais das mesmas pessoas são
-- classificadas em comercial (outro vendedor/link) e digital (selfcheckout).
-- Período da campanha parametrizado no filtro de dt_ordered_at (2026-07-15).

WITH cb_pessoas AS (
  SELECT DISTINCT
    id_person,
    LOWER(nm_person_email) AS email,
    REGEXP_REPLACE(cd_person_cleaned_phone_number, r'[^0-9]', '') AS tel
  FROM `bp-datawarehouse.staging.int_pipedrive_analytics`
  WHERE nm_title LIKE 'UPSELL |%'
),

vendas AS (
  SELECT
    t.id_transaction,
    t.dt_ordered_at,
    t.vl_payment_gross,
    t.nm_gateway_plan,
    t.bl_is_commercial_channel,
    t.nm_salesman,
    t.nm_pptc_tracking_name,
    t.nm_pptc_tracking_publisher,
    -- COALESCE: com tracking/produto/oferta todos NULL o LIKE vira NULL e a
    -- venda sumiria de todos os buckets (gotcha bq-regras.md)
    COALESCE(
      UPPER(t.nm_pptc_tracking_name) LIKE '%C0113%'
      OR LOWER(t.nm_gateway_product) LIKE '%lambda%'
      OR LOWER(t.nm_gateway_offer) LIKE '%lambda%', FALSE
    ) AS eh_lambda,
    LOWER(c.nm_email) AS email,
    REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]', '') AS tel
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.dt_ordered_at >= '2026-07-15'  -- início da campanha
),

-- match por email e telefone em joins separados (OR no ON vira cross-join)
match AS (
  SELECT p.id_person, v.*
  FROM cb_pessoas p
  JOIN vendas v ON p.email = v.email AND p.email IS NOT NULL AND p.email != ''
  UNION DISTINCT
  SELECT p.id_person, v.*
  FROM cb_pessoas p
  JOIN vendas v ON p.tel = v.tel AND p.tel IS NOT NULL AND p.tel != ''
),

por_pessoa AS (
  SELECT
    id_person,
    COUNTIF(eh_lambda) AS qt_lambda,
    SUM(IF(eh_lambda, vl_payment_gross, 0)) AS vl_lambda,
    COUNTIF(NOT eh_lambda AND bl_is_commercial_channel) AS qt_outro_comercial,
    SUM(IF(NOT eh_lambda AND bl_is_commercial_channel, vl_payment_gross, 0)) AS vl_outro_comercial,
    COUNTIF(NOT eh_lambda AND NOT bl_is_commercial_channel) AS qt_digital,
    SUM(IF(NOT eh_lambda AND NOT bl_is_commercial_channel, vl_payment_gross, 0)) AS vl_digital
  FROM match
  GROUP BY 1
)

-- resumo por desfecho (prioridade: lambda > outro comercial > digital);
-- para a lista pessoa a pessoa, trocar este SELECT por `SELECT * FROM por_pessoa`
SELECT
  CASE
    WHEN p.qt_lambda > 0 THEN '1. comprou via Lambda (C0113)'
    WHEN p.qt_outro_comercial > 0 THEN '2. comprou por outro vendedor/link comercial'
    WHEN p.qt_digital > 0 THEN '3. comprou selfcheckout/digital'
  END AS desfecho,
  COUNT(*) AS qt_pessoas,
  ROUND(COUNT(*) / (SELECT COUNT(*) FROM cb_pessoas), 3) AS pct_da_base,
  SUM(p.qt_lambda + p.qt_outro_comercial + p.qt_digital) AS qt_vendas,
  ROUND(SUM(p.vl_lambda + p.vl_outro_comercial + p.vl_digital), 0) AS vl_total
FROM por_pessoa p
GROUP BY 1

UNION ALL

SELECT
  '4. nao comprou nada no periodo',
  (SELECT COUNT(*) FROM cb_pessoas) - (SELECT COUNT(DISTINCT id_person) FROM por_pessoa),
  ROUND(1 - (SELECT COUNT(DISTINCT id_person) FROM por_pessoa) / (SELECT COUNT(*) FROM cb_pessoas), 3),
  0,
  0
ORDER BY 1
