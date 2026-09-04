-- Base 1 linha por comprador da Coleção Brasil: A Última Cruzada (lançada 01/09/2026)
-- Chave de pessoa: e-mail normalizado (cobre multi-conta por e-mail)
CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_uc_compradores` AS

WITH uc_tx AS (
  SELECT t.*, LOWER(TRIM(c.nm_email)) AS email
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE DATE(t.dt_ordered_at) >= '2026-08-25'
    AND ( t.nm_gateway_plan LIKE 'colecao-brasil%'
       OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_product,'')), r'cole[cç][aã]o brasil') )
    AND t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
),

compra AS (
  SELECT
    email,
    MIN(dt_ordered_at)                                   AS dt_compra_uc,
    SUM(vl_payment_gross)                                AS vl_uc,
    MAX(qt_installments)                                  AS qt_parcelas_uc,
    LOGICAL_OR(bl_is_commercial_channel)                 AS bl_comercial,
    STRING_AGG(DISTINCT nm_gateway_plan, ' | ')          AS planos_uc,
    STRING_AGG(DISTINCT nm_gateway_offer, ' | ')         AS ofertas_uc,
    ANY_VALUE(nm_salesman)                               AS nm_salesman,
    ANY_VALUE(nm_pptc_checkout_name)                     AS checkout,
    ANY_VALUE(nm_pptc_tracking_publisher)                AS tracking_publisher,
    ANY_VALUE(nm_pptc_utm_campaign)                      AS utm_campaign,
    ANY_VALUE(nm_lead_last_tracking)                     AS lead_last_tracking,
    ANY_VALUE(nm_payment_method)                         AS nm_payment_method,
    ANY_VALUE(nm_credit_card_bin)                        AS nm_credit_card_bin,
    MAX(id_gateway_customer)                             AS id_gateway_customer
  FROM uc_tx
  WHERE email IS NOT NULL
  GROUP BY email
),

-- Blacklist de planos que NÃO são membership (produtos avulsos/livros)
-- Whitelist de membership conforme bq-regras.md
hist AS (
  SELECT
    LOWER(TRIM(c.nm_email)) AS email,
    MIN(t.dt_ordered_at)                                        AS dt_primeira_compra,
    COUNT(*)                                                    AS qt_compras_ant,
    SUM(t.vl_payment_gross)                                     AS vl_ltv_ant,
    MAX(t.vl_payment_gross)                                     AS vl_maior_ticket_ant,
    COUNTIF(t.bl_is_commercial_channel)                         AS qt_compras_comercial_ant,
    -- vitalício GBB (excluindo produtos físicos que vêm com a flag ligada)
    LOGICAL_OR(
      t.bl_lifetime_offer
      AND ( t.nm_gateway_plan IN ('good','better','best','black')
            OR LOWER(COALESCE(t.nm_gateway_product,'')) LIKE '%vital%'
            OR LOWER(COALESCE(t.nm_gateway_product,'')) LIKE '%membro fundador%')
      AND NOT REGEXP_CONTAINS(COALESCE(t.nm_gateway_plan,''), r'colecao-brasil|odisseia|clube-do-livro')
    )                                                           AS bl_vitalicio,
    LOGICAL_OR(COALESCE(t.nm_gateway_plan,'') LIKE 'mecenas%')   AS bl_mecenas,
    LOGICAL_OR(COALESCE(t.nm_gateway_plan,'') IN ('clube-do-livro','clube-do-livro-basico')) AS bl_cdl,
    LOGICAL_OR(COALESCE(t.nm_gateway_plan,'') LIKE 'livro-odisseia%' OR COALESCE(t.nm_gateway_plan,'')='odisseia-curso-avulso') AS bl_odisseia,
    LOGICAL_OR(COALESCE(t.nm_gateway_plan,'') IN ('bitcoin','ciencia-politica','geopolitica','metodo-bp','travessia','travessia-familia')) AS bl_certificacao,
    LOGICAL_OR(COALESCE(t.nm_gateway_plan,'') LIKE '%teller%')   AS bl_teller
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND NOT ( t.nm_gateway_plan LIKE 'colecao-brasil%'
              OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_product,'')), r'cole[cç][aã]o brasil') )
    AND LOWER(TRIM(c.nm_email)) IN (SELECT email FROM compra)
  GROUP BY email
),

-- Membership ativa hoje (whitelist de tiers, exclui produtos avulsos)
memb AS (
  SELECT
    LOWER(TRIM(c.nm_email)) AS email,
    LOGICAL_OR(
      s.nm_status IN ('active','wo renewal')
      AND s.dt_started_at <= CURRENT_DATETIME() AND s.dt_expires_in >= CURRENT_DATETIME()
      AND REGEXP_CONTAINS(LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)),
            r'^(bp-)?(good|better|best|black|supporter|mecenas|intermediario|premium|essencial|economico|basico|apoiador|originais|originals|fraterno|combo-religioso|extensao-assinatura|bolsa-mecenas)')
      AND LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) NOT LIKE '%teller%'
      AND LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) <> 'essencial-estudar-bem'
    ) AS bl_membro_ativo,
    STRING_AGG(DISTINCT CASE
      WHEN s.nm_status IN ('active','wo renewal') AND s.dt_expires_in >= CURRENT_DATETIME()
       AND REGEXP_CONTAINS(LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)),
            r'^(bp-)?(good|better|best|black|supporter|mecenas|intermediario|premium|essencial|economico|basico|apoiador|originais|originals|fraterno|combo-religioso|extensao-assinatura|bolsa-mecenas)')
       AND LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) NOT LIKE '%teller%'
      THEN s.nm_plan_label END, ' | ') AS planos_ativos,
    MIN(s.dt_started_at) AS dt_primeira_assinatura
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE s.nm_type = 'paid'
    AND LOWER(TRIM(c.nm_email)) IN (SELECT email FROM compra)
  GROUP BY email
),

usr AS (
  SELECT LOWER(TRIM(nm_email)) AS email, id_user, cd_address_state, nm_gender_inferred,
         dt_birthday, nm_profession, arr_roles
  FROM `bp-datawarehouse.masterdata.dim_user`
  WHERE LOWER(TRIM(nm_email)) IN (SELECT email FROM compra)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY LOWER(TRIM(nm_email)) ORDER BY id_user) = 1
),

pp AS (
  SELECT p.id_user, p.cd_income_decile, p.vl_income_per_capita
  FROM `bp-datawarehouse.datamart.dtm_purchasing_power` p
  JOIN usr ON usr.id_user = p.id_user
),

cartao AS (
  SELECT LOWER(TRIM(nm_email)) AS email, MAX(nm_credit_card_level_max) AS nivel_cartao
  FROM `bp-datawarehouse.staging.int_credit_card_level`
  WHERE LOWER(TRIM(nm_email)) IN (SELECT email FROM compra)
  GROUP BY email
),

eng AS (
  SELECT LOWER(TRIM(nm_email)) AS email,
    COUNT(DISTINCT CASE WHEN DATE(dt_created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) THEN DATE(dt_created_at) END) AS qt_dias_ativos_90d,
    ROUND(SUM(CASE WHEN DATE(dt_created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) THEN vl_watch_time_seconds END)/3600, 1) AS hr_assistidas_90d,
    ROUND(SUM(vl_watch_time_seconds)/3600, 1) AS hr_assistidas_total,
    MAX(DATE(dt_created_at)) AS dt_ultima_sessao
  FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
  WHERE LOWER(TRIM(nm_email)) IN (SELECT email FROM compra)
  GROUP BY email
)

SELECT
  co.*,
  ct.nm_name, ct.cd_address_state AS uf_contato, ct.dt_created_at AS dt_cadastro_contato,
  h.dt_primeira_compra, h.qt_compras_ant, h.vl_ltv_ant, h.vl_maior_ticket_ant,
  h.qt_compras_comercial_ant, h.bl_vitalicio, h.bl_mecenas, h.bl_cdl, h.bl_odisseia,
  h.bl_certificacao, h.bl_teller,
  DATE_DIFF(DATE(co.dt_compra_uc), DATE(h.dt_primeira_compra), DAY) AS qt_dias_de_casa,
  COALESCE(m.bl_membro_ativo, FALSE) AS bl_membro_ativo, m.planos_ativos, m.dt_primeira_assinatura,
  u.id_user, u.nm_gender_inferred, u.dt_birthday, u.nm_profession, u.arr_roles,
  pp.cd_income_decile, pp.vl_income_per_capita,
  ca.nivel_cartao,
  e.qt_dias_ativos_90d, e.hr_assistidas_90d, e.hr_assistidas_total, e.dt_ultima_sessao
FROM compra co
LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` ct ON ct.id_gateway_customer = co.id_gateway_customer
LEFT JOIN hist h USING (email)
LEFT JOIN memb m USING (email)
LEFT JOIN usr  u USING (email)
LEFT JOIN pp   ON pp.id_user = u.id_user
LEFT JOIN cartao ca USING (email)
LEFT JOIN eng  e USING (email)
