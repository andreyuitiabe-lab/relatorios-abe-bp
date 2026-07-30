-- Vendas COMERCIAIS não-Lambda das pessoas da lista "Conteúdo bloqueado",
-- com timing vs entrada na lista (criação do 1º card CB da pessoa).
-- Leitura (30/07/2026): 65 vendas / R$ 62,8k ANTES de entrar na lista
-- (higiene de lista — compradores recentes entrando na base da Lambda) vs
-- 17 vendas / R$ 25,1k DEPOIS (concorrência real de canal com a Lambda).
-- Trocar o SELECT final pelos agregados comentados conforme a pergunta.

WITH cb_pessoas AS (
  SELECT
    LOWER(nm_person_email) AS email,
    REGEXP_REPLACE(cd_person_cleaned_phone_number, r'[^0-9]', '') AS tel,
    MIN(dt_created_at) AS dt_entrou_lista
  FROM `bp-datawarehouse.staging.int_pipedrive_analytics`
  WHERE nm_title LIKE 'UPSELL |%'
  GROUP BY 1, 2
),

vendas AS (
  SELECT
    t.id_transaction,
    t.dt_ordered_at,
    t.vl_payment_gross,
    t.nm_gateway_plan,
    t.nm_plan_label,
    t.bl_lifetime_offer,
    t.nm_salesman,
    t.nm_pptc_tracking_name,
    LOWER(c.nm_email) AS email,
    REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]', '') AS tel
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.dt_ordered_at >= '2026-07-15'  -- início da campanha
    AND t.bl_is_commercial_channel = TRUE
    -- excluir vendas Lambda (COALESCE: gotcha de NULL em LIKE, bq-regras.md)
    AND NOT COALESCE(
      UPPER(t.nm_pptc_tracking_name) LIKE '%C0113%'
      OR LOWER(t.nm_gateway_product) LIKE '%lambda%'
      OR LOWER(t.nm_gateway_offer) LIKE '%lambda%', FALSE
    )
),

-- match por email e telefone em joins separados (OR no ON vira cross-join)
match AS (
  SELECT v.*, p.dt_entrou_lista
  FROM cb_pessoas p
  JOIN vendas v ON p.email = v.email AND p.email IS NOT NULL AND p.email != ''
  UNION DISTINCT
  SELECT v.*, p.dt_entrou_lista
  FROM cb_pessoas p
  JOIN vendas v ON p.tel = v.tel AND p.tel IS NOT NULL AND p.tel != ''
),

match_nodup AS (
  SELECT *
  FROM match
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id_transaction ORDER BY dt_entrou_lista) = 1
)

SELECT
  IF(dt_ordered_at >= dt_entrou_lista,
     'depois de entrar na lista', 'antes de entrar na lista') AS timing,
  COALESCE(
    nm_salesman,
    CONCAT('(link) ', COALESCE(REGEXP_EXTRACT(UPPER(nm_pptc_tracking_name), r'([AC]\d{4})'), '?'))
  ) AS vendedor,
  id_transaction,
  dt_ordered_at,
  dt_entrou_lista,
  nm_plan_label,
  bl_lifetime_offer,
  vl_payment_gross
FROM match_nodup
ORDER BY timing, vl_payment_gross DESC

-- Agregado por timing:
--   SELECT IF(dt_ordered_at >= dt_entrou_lista, 'depois', 'antes') timing,
--          COUNT(*) qt, ROUND(SUM(vl_payment_gross)) vl, COUNTIF(bl_lifetime_offer) qt_vitalicios
--   FROM match_nodup GROUP BY 1
