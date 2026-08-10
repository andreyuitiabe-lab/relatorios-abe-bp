-- Base de qualificação Mecenas: uma linha por PESSOA REAL (id_person), com label e features.
-- Materializa em bp-staging.dbt_abe.tb_mecenas_qualificacao_base para reuso.
--
-- ⚠️ Grain = id_person, não e-mail. Muita gente paga com e-mails diferentes; agregar por
-- e-mail infla a contagem de doadores e subestima quanto cada pessoa realmente doou.
-- Resolução via dim_person_identity por e-mail, telefone OU CPF (o que casar primeiro).
-- Quem não resolve cai num id sintético a partir do e-mail, para não sumir da base.
--
-- ⚠️ TRÊS populações separadas (ver bloco de flags abaixo), nunca somar:
--   bl_is_mecenas    = BOLSA, o doador clássico (>= R$ 1.000). É a base da análise de perfil.
--   bl_is_solidario  = campanha atual (jul/2026+), de ~R$ 30/mês sem teto.
--   bl_is_order_bump = R$ 180 no checkout de outro produto. Não é doador.
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
    -- ── Três populações distintas, nunca misturar ─────────────────────────────
    -- O Mecenas nasceu como PATROCÍNIO DE BOLSA: 1 bolsa = R$ 1.188 (com desconto) ou
    -- R$ 1.668. Todo o histórico 2021–2026 é assim (Bolsas, Missão Mecenas, Funding,
    -- Patrono, Certificação). É esse o "doador clássico" da análise de perfil.

    -- 1) BOLSA — doador clássico. Corte em R$ 1.000 (decisão de negócio, ago/2026): abaixo
    --    disso não existe bolsa inteira. ⚠️ Deixa fora o pagamento fracionado de 1 bolsa
    --    (ex.: 2× R$ 594); perda pequena, aceitável para não contaminar o perfil.
    (
      LOWER(COALESCE(t.nm_gateway_product, '')) NOT LIKE '%solid%'
      AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%solid%'
      AND t.nm_gateway_plan <> 'mecenas_mecenas-solidario-premium'
      AND t.nm_gateway_product NOT LIKE '%Mecenas Patrono%'    -- foi para o Solidário (mapeamento)
      AND t.nm_gateway_product NOT LIKE '%Mecenas Apoiador%'   -- idem
      AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump%'
      AND LOWER(COALESCE(t.nm_gateway_product, '')) NOT LIKE '%order bump%'
      AND ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
        OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
      AND t.vl_payment_gross >= 1000
    ) AS bl_bolsa,

    -- 2) SOLIDÁRIO — a campanha atual. Segue o MAPEAMENTO DO SISTEMA (produtos_bp/mappings),
    --    que agrupa 5 produtos sob "Mecenas Solidário" — decisão do negócio (10/ago/2026),
    --    para o número bater com o dashboard do marketing-bp:
    --      Brasil Paralelo - Mecenas Solidário            (R$ 27/97 mensal; R$ 358,80/718,80 anual)
    --      Brasil Paralelo - Mecenas Solidário + Premium  (R$ 1.078,80, com Premium incluso)
    --      Comercial - Mecenas Solidário                  ("N reais por dia"; meses de formação)
    --      Comercial - Mecenas Patrono                    (R$ 36.000 e R$ 72.000)
    --      Comercial - Mecenas Apoiador                   (R$ 4.500 e R$ 9.000)
    --    ⚠️ Identificar por PRODUTO, nunca por valor: Solidário vai de R$ 27 a R$ 72.000, então
    --    qualquer corte de valor separa errado.
    --    ⚠️ Patrono e Apoiador são 7 transações mas ~63% da receita do grupo — SEMPRE reportar
    --    mediana e distribuição, nunca média. A média deste grupo não descreve ninguém.
    --    ⚠️ 1 Apoiador é de 09/jun/2026, anterior ao lançamento do Solidário (25/jul) — o
    --    mapeamento é por produto, não por janela de campanha.
    (
      LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%solid%'
      OR LOWER(COALESCE(t.nm_gateway_offer, '')) LIKE '%solid%'
      OR t.nm_gateway_plan = 'mecenas_mecenas-solidario-premium'
      OR t.nm_gateway_product LIKE '%Mecenas Patrono%'
      OR t.nm_gateway_product LIKE '%Mecenas Apoiador%'
    ) AS bl_solidario,

    -- 3) ORDER BUMP DE MECENAS — R$ 180 (R$ 15/mês) marcado no checkout de outro produto.
    --    NÃO é doador. Um dos dois não tem "order bump" no nome da OFERTA, daí testar também
    --    o produto. ⚠️ Restringir a Mecenas: order bump de CDL/BP Clube é compra legítima e
    --    deve continuar contando no histórico (vl_total_outras), senão o gasto prévio afunda.
    (
      (LOWER(COALESCE(t.nm_gateway_offer, '')) LIKE '%order bump%'
        OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%order bump%')
      AND (LOWER(COALESCE(t.nm_gateway_offer, '')) LIKE '%mecenas%'
        OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%'
        OR t.nm_gateway_plan LIKE 'mecenas%')
    ) AS bl_order_bump
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN contato ct ON ct.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
),

pessoa AS (
  SELECT
    id_person,
    MAX(bl_bolsa)                                            AS bl_is_mecenas,     -- doador clássico
    MAX(bl_solidario)                                        AS bl_is_solidario,
    MAX(bl_order_bump)                                       AS bl_is_order_bump,
    MIN(dt_ordered_at)                                       AS dt_primeira_compra,
    MAX(dt_ordered_at)                                       AS dt_ultima_compra,
    MIN(IF(bl_bolsa, dt_ordered_at, NULL))                   AS dt_primeiro_mecenas,
    MIN(IF(bl_solidario, dt_ordered_at, NULL))               AS dt_primeiro_solidario,
    MAX(IF(bl_bolsa, vl_payment_gross, NULL))                AS vl_maior_tx_mecenas,
    MAX(IF(bl_solidario, vl_payment_gross, NULL))            AS vl_maior_tx_solidario,
    SUM(IF(bl_bolsa, vl_payment_gross, 0))                   AS vl_total_mecenas,
    SUM(IF(bl_solidario, vl_payment_gross, 0))               AS vl_total_solidario,
    COUNTIF(bl_bolsa)                                        AS qt_tx_mecenas,
    COUNTIF(bl_solidario)                                    AS qt_tx_solidario,
    COUNTIF(NOT bl_bolsa AND NOT bl_solidario AND NOT bl_order_bump) AS qt_tx_outras,
    SUM(IF(NOT bl_bolsa AND NOT bl_solidario AND NOT bl_order_bump, vl_payment_gross, 0)) AS vl_total_outras,
    MAX(IF(NOT bl_bolsa AND NOT bl_solidario AND NOT bl_order_bump, vl_payment_gross, 0)) AS vl_maior_tx_outras,
    MAX(IF(NOT bl_bolsa AND NOT bl_solidario AND nm_gateway_plan = 'black', 1, 0))              AS bl_black,
    MAX(IF(NOT bl_bolsa AND NOT bl_solidario AND bl_lifetime_offer, 1, 0))                      AS bl_vitalicio,
    MAX(IF(NOT bl_bolsa AND NOT bl_solidario AND nm_gateway_plan IN
      ('bitcoin','ciencia-politica','geopolitica','metodo-bp','travessia','travessia-familia'), 1, 0)) AS bl_certificacao,
    MAX(IF(NOT bl_bolsa AND NOT bl_solidario AND nm_gateway_plan LIKE 'clube-do-livro%', 1, 0)) AS bl_cdl,
    MAX(IF(NOT bl_bolsa AND NOT bl_solidario AND nm_gateway_plan LIKE '%teller%', 1, 0))        AS bl_teller,
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
