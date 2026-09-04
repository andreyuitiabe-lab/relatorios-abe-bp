-- Funil de abordagem Zenvia do CBR: disparo -> resposta -> venda
--
-- ⚠️ Rev. 04/09/2026 (pós-auditoria). A versão anterior classificava o prospect por
-- `MIN(template)` e jogava no bucket "broadcast" TODO prospect tocado pelo disparo,
-- inclusive os que também tiveram atendimento de vendedor. Os 384 prospects mistos
-- (6,6% do bucket) concentravam 96,8% das respostas e 82,6% das vendas atribuídas ao
-- broadcast — a taxa de resposta do disparo aparecia como 5,3% em vez de 0,18%.
-- Agora os buckets são mutuamente exclusivos e explícitos.
--
-- ⚠️ Também marca se a 1ª abordagem veio ANTES da compra. Sem essa guarda, metade das
-- vendas "abordado -> digital" era de gente que o Comercial abordou depois de já ter
-- comprado (correndo atrás da lista), não gente que o Comercial aqueceu.

CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_uc_abordagens` AS

WITH ab AS (
  SELECT
    a.id_prospect, a.id_approach, a.dt_approach_start,
    a.qt_seller_interactions, a.qt_prospect_interactions,
    REGEXP_REPLACE(a.nm_conversation, r'\s+', ' ') AS conv
  FROM `bp-datawarehouse.masterdata.dim_zenvia_approaches` a
  WHERE DATE(a.dt_approach_start) >= '2026-09-01'   -- lançamento; janela aberta até hoje
    AND REGEXP_CONTAINS(LOWER(COALESCE(a.nm_conversation, '')), r'[uú]ltima cruzada|cole[cç][aã]o brasil')
),

class AS (
  SELECT *,
    -- a peça de disparo em massa: texto longo com imagem e CTA "falar com um consultor"
    LOWER(conv) LIKE '%esse dia chegou%' AS bl_broadcast,
    -- Assinatura da abertura, para detectar script repetido (ver `script` abaixo).
    -- ⚠️ Pula os 40 primeiros caracteres: quase todo script começa com o PRIMEIRO NOME do
    -- cliente ("Alexandre, esse dia chegou"), então comparar o início faz um script de massa
    -- parecer mensagem única. O miolo da frase é o que se repete.
    SUBSTR(REGEXP_REPLACE(conv, r'^seller: (https?://\S+ )?', ''), 40, 110) AS abertura
  FROM ab
),

-- Quantas vezes cada abertura se repete no período: separa script de massa de conversa real
script AS (
  SELECT abertura, COUNT(DISTINCT id_prospect) AS qt_prospects_mesma_abertura
  FROM class GROUP BY 1
),

prospect AS (
  SELECT
    c.id_prospect,
    MIN(c.dt_approach_start) AS dt_primeira_abordagem,
    MIN(IF(c.bl_broadcast, c.dt_approach_start, NULL)) AS dt_primeiro_broadcast,
    MIN(IF(NOT c.bl_broadcast, c.dt_approach_start, NULL)) AS dt_primeiro_toque_vendedor,
    MAX(c.qt_prospect_interactions) AS max_resposta_cliente,
    SUM(c.qt_seller_interactions) AS interacoes_vendedor,
    LOGICAL_OR(c.bl_broadcast) AS bl_recebeu_broadcast,
    LOGICAL_OR(NOT c.bl_broadcast) AS bl_recebeu_toque_vendedor,
    -- a abordagem que abriu a relação era script de massa?
    MAX(s.qt_prospects_mesma_abertura) AS qt_prospects_mesma_abertura
  FROM class c
  JOIN script s USING (abertura)
  GROUP BY 1
),

bucket AS (
  SELECT *,
    CASE
      WHEN bl_recebeu_broadcast AND NOT bl_recebeu_toque_vendedor THEN '1. Disparo em massa (só a peça)'
      WHEN bl_recebeu_broadcast AND bl_recebeu_toque_vendedor     THEN '2. Disparo + atendimento de vendedor'
      ELSE '3. Abordagem do vendedor (sem disparo)'
    END AS bucket,
    qt_prospects_mesma_abertura >= 20 AS bl_abertura_scriptada
  FROM prospect
),

zc AS (
  SELECT id_prospect, cd_cleaned_phone_number AS fone, nm_contact_email,
         nm_stage AS etapa_atual, TRIM(nm_group) AS grupo
  FROM `bp-datawarehouse.masterdata.dim_zenvia_contacts`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id_prospect ORDER BY dt_last_status_updated_at DESC) = 1
),

compradores AS (
  SELECT c.cd_cleaned_phone_number AS fone, b.bl_comercial, b.vl_uc, b.dt_compra_uc
  FROM `bp-staging.dbt_abe.tb_uc_compradores` b
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE c.cd_cleaned_phone_number IS NOT NULL
)

SELECT
  b.*,
  zc.fone, zc.etapa_atual, zc.grupo,
  cp.fone IS NOT NULL                                     AS bl_comprou,
  cp.bl_comercial, cp.vl_uc, cp.dt_compra_uc,
  -- guarda de causalidade: a abordagem precede a compra?
  cp.fone IS NOT NULL AND cp.dt_compra_uc >= b.dt_primeira_abordagem
                                                          AS bl_comprou_apos_abordagem
FROM bucket b
LEFT JOIN zc USING (id_prospect)
LEFT JOIN compradores cp ON cp.fone = zc.fone
