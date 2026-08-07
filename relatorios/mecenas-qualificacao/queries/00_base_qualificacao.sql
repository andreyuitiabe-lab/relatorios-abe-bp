-- Base de qualificação Mecenas: uma linha por PESSOA REAL (id_person), com label e features.
-- Materializa em bp-staging.dbt_abe.tb_mecenas_qualificacao_base para reuso.
--
-- ⚠️ Grain = id_person, não e-mail. Muita gente paga com e-mails diferentes; agregar por
-- e-mail infla a contagem de doadores e subestima quanto cada pessoa realmente doou.
-- Resolução via dim_person_identity por e-mail, telefone OU CPF (o que casar primeiro).
-- Quem não resolve cai num id sintético a partir do e-mail, para não sumir da base.
--
-- ⚠️ Doador = compra Mecenas >= R$ 300. Dois order bumps precisam sair e só um tem
-- "order bump" no nome da oferta:
--   (a) BP Essencial - 20%Off Order Bump Mecenas → pega pelo nome
--   (b) Brasil Paralelo/Comercial - Mecenas Order Bump (R$180 = R$15/mês) → ofertas
--       "Adicione + R$ 15/mês..." / "Upsell pós compra...". Só o corte de valor pega.
--
-- ⚠️ id_person NÃO é estável entre runs do dbt (ver wiki dbt-identity-graph) — sempre
-- reresolver via JOIN, nunca armazenar em modelo incremental.

CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_mecenas_qualificacao_base` AS

WITH ident AS (
  SELECT nm_identifier, nm_identifier_type, id_person
  FROM `bp-datawarehouse.masterdata.dim_person_identity`
),

-- resolve cada conta do gateway para uma pessoa real
contato AS (
  SELECT
    c.id_gateway_customer,
    LOWER(c.nm_email) AS email,
    COALESCE(
      pe.id_person,
      pp.id_person,
      pc.id_person,
      CONCAT('email::', LOWER(c.nm_email))     -- fallback: não resolveu no grafo
    ) AS id_person
  FROM `bp-datawarehouse.masterdata.dim_contact` c
  LEFT JOIN ident pe
    ON pe.nm_identifier_type = 'email' AND pe.nm_identifier = LOWER(c.nm_email)
  LEFT JOIN ident pp
    ON pp.nm_identifier_type = 'phone' AND pp.nm_identifier = c.cd_cleaned_phone_number
  LEFT JOIN ident pc
    ON pc.nm_identifier_type = 'cpf' AND pc.nm_identifier = c.cd_cpf
  WHERE c.nm_email IS NOT NULL
),

tx AS (
  SELECT
    ct.id_person,
    t.dt_ordered_at,
    t.vl_payment_gross,
    t.nm_gateway_plan,
    t.bl_lifetime_offer,
    t.bl_is_commercial_channel,
    (
      ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
        OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
      AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump%'
      AND t.vl_payment_gross >= 300
    ) AS bl_mecenas
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN contato ct ON ct.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
),

pessoa AS (
  SELECT
    id_person,
    MAX(bl_mecenas)                                          AS bl_is_mecenas,
    MIN(dt_ordered_at)                                       AS dt_primeira_compra,
    MAX(dt_ordered_at)                                       AS dt_ultima_compra,
    MIN(IF(bl_mecenas, dt_ordered_at, NULL))                 AS dt_primeiro_mecenas,
    MAX(IF(bl_mecenas, vl_payment_gross, NULL))              AS vl_maior_tx_mecenas,
    SUM(IF(bl_mecenas, vl_payment_gross, 0))                 AS vl_total_mecenas,
    COUNTIF(bl_mecenas)                                      AS qt_tx_mecenas,
    COUNTIF(NOT bl_mecenas)                                  AS qt_tx_outras,
    SUM(IF(NOT bl_mecenas, vl_payment_gross, 0))             AS vl_total_outras,
    MAX(IF(NOT bl_mecenas, vl_payment_gross, 0))             AS vl_maior_tx_outras,
    MAX(IF(NOT bl_mecenas AND nm_gateway_plan = 'black', 1, 0))              AS bl_black,
    MAX(IF(NOT bl_mecenas AND bl_lifetime_offer, 1, 0))                      AS bl_vitalicio,
    MAX(IF(NOT bl_mecenas AND nm_gateway_plan IN
      ('bitcoin','ciencia-politica','geopolitica','metodo-bp','travessia','travessia-familia'), 1, 0)) AS bl_certificacao,
    MAX(IF(NOT bl_mecenas AND nm_gateway_plan LIKE 'clube-do-livro%', 1, 0)) AS bl_cdl,
    MAX(IF(NOT bl_mecenas AND nm_gateway_plan LIKE '%teller%', 1, 0))        AS bl_teller,
    MAX(IF(bl_is_commercial_channel, 1, 0))                                  AS bl_ja_comprou_comercial,
    COUNT(DISTINCT id_person)                                                AS _chk
  FROM tx
  GROUP BY id_person
),

-- e-mails da pessoa (para casar com fontes que só têm e-mail)
emails AS (
  SELECT id_person, ARRAY_AGG(DISTINCT email IGNORE NULLS) AS arr_email
  FROM contato
  GROUP BY id_person
),

usr AS (
  SELECT
    e.id_person,
    ANY_VALUE(u.id_user)             AS id_user,
    ANY_VALUE(u.nm_gender_inferred)  AS nm_gender_inferred,
    ANY_VALUE(u.nm_profession)       AS nm_profession,
    MIN(u.dt_birthday)               AS dt_birthday
  FROM emails e, UNNEST(e.arr_email) em
  JOIN `bp-datawarehouse.masterdata.dim_user` u ON LOWER(u.nm_email) = em
  GROUP BY e.id_person
),

cartao AS (
  SELECT e.id_person, MAX(cc.nm_credit_card_level_max) AS nm_credit_card_level_max
  FROM emails e, UNNEST(e.arr_email) em
  JOIN `bp-datawarehouse.staging.int_credit_card_level` cc ON LOWER(cc.nm_email) = em
  GROUP BY e.id_person
),

cnpj AS (
  SELECT
    e.id_person,
    MAX(d.pc_levenshtein_similarity_member_partner) AS pc_similaridade,
    MAX(d.qt_companies)                             AS qt_empresas,
    MAX(d.vl_share_capital_total)                   AS vl_capital_social,
    ANY_VALUE(d.arr_nm_company_size)                AS arr_porte,
    ANY_VALUE(d.arr_nm_cnae_section)                AS arr_cnae_section,
    ANY_VALUE(d.arr_nm_cnae_division)               AS arr_cnae_division
  FROM emails e, UNNEST(e.arr_email) em
  JOIN `bp-datawarehouse.masterdata.dim_entrepreneurs` d ON LOWER(d.nm_email) = em
  GROUP BY e.id_person
),

renda AS (
  SELECT u.id_person, MAX(pp.cd_income_decile) AS cd_income_decile
  FROM usr u
  JOIN `bp-datawarehouse.datamart.dtm_purchasing_power` pp ON pp.id_user = u.id_user
  GROUP BY u.id_person
),

ativo AS (
  SELECT ct.id_person, MAX(1) AS bl_membro_ativo
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  JOIN contato ct ON ct.id_gateway_customer = s.id_gateway_customer
  WHERE s.nm_status IN ('active', 'wo renewal')
    AND s.nm_type = 'paid'
    AND s.dt_started_at <= CURRENT_DATETIME()
    AND s.dt_expires_in >= CURRENT_DATETIME()
  GROUP BY ct.id_person
)

SELECT
  p.* EXCEPT (_chk),
  e.arr_email,
  e.arr_email[SAFE_OFFSET(0)] AS email,       -- compatibilidade com queries antigas
  ARRAY_LENGTH(e.arr_email)   AS qt_contas,   -- quantas contas a pessoa tem
  u.id_user,
  u.nm_gender_inferred,
  u.nm_profession,
  DATE_DIFF(CURRENT_DATE(), DATE(u.dt_birthday), YEAR) AS qt_idade,
  r.cd_income_decile,
  ct.nm_credit_card_level_max,
  cj.pc_similaridade,
  cj.qt_empresas,
  cj.vl_capital_social,
  cj.arr_porte,
  cj.arr_cnae_section,
  cj.arr_cnae_division,
  COALESCE(a.bl_membro_ativo, 0) AS bl_membro_ativo,
  DATE_DIFF(CURRENT_DATE(), DATE(p.dt_primeira_compra), DAY) AS qt_dias_casa
FROM pessoa p
LEFT JOIN emails e USING (id_person)
LEFT JOIN usr    u USING (id_person)
LEFT JOIN renda  r USING (id_person)
LEFT JOIN cartao ct USING (id_person)
LEFT JOIN cnpj   cj USING (id_person)
LEFT JOIN ativo  a USING (id_person)
