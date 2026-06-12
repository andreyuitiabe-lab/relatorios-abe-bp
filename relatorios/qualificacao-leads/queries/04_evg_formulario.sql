-- PASSO 4: Formulário EVG — respostas × conversão
-- Objetivo: identificar quais respostas do formulário predizem conversão
-- Campanha: EVG (Brasil Evangélico, ~23/05/2026+)
--
-- ⚠️ Se tb_lead_surveys não cobrir EVG, rodar primeiro:
--    SELECT DISTINCT nm_campaign_tag FROM `bp-staging.dbt_abe.tb_lead_surveys`
--    para ver quais campanhas têm dados.
--
-- ⚠️ Se o formulário EVG for um Facebook Lead Form (não survey interno),
--    verificar se existe tabela separada, ex: bp-lake.marketing.lead_form_responses

-- 4a. Distribuição de respostas por pergunta (para entender o formulário)
SELECT
  nm_question,
  nm_answer,
  COUNT(*)                                        AS total_respostas,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY nm_question) * 100, 1)
                                                  AS pct_da_pergunta
FROM `bp-staging.dbt_abe.tb_lead_surveys`
WHERE nm_campaign_tag = 'EVG'
GROUP BY 1, 2
ORDER BY nm_question, total_respostas DESC;

-- -----------------------------------------------------------------------

-- 4b. Respostas × conversão (lift por resposta)
WITH

respostas AS (
  SELECT
    LOWER(TRIM(nm_email))                         AS nm_email,
    nm_question,
    nm_answer,
    DATE(dt_answered_at)                          AS dt_respondeu
  FROM `bp-staging.dbt_abe.tb_lead_surveys`
  WHERE nm_campaign_tag = 'EVG'
),

conversoes AS (
  SELECT DISTINCT
    LOWER(TRIM(nm_email))                         AS nm_email,
    MIN(DATE(dt_ordered_at))                      AS dt_compra
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_is_renovation = FALSE
    AND DATE(dt_ordered_at) >= '2026-05-23'  -- início EVG
  GROUP BY 1
)

SELECT
  r.nm_question,
  r.nm_answer,
  COUNT(DISTINCT r.nm_email)                      AS leads_com_resposta,
  COUNTIF(c.nm_email IS NOT NULL
    AND c.dt_compra >= r.dt_respondeu)            AS convertidos,
  ROUND(
    COUNTIF(c.nm_email IS NOT NULL AND c.dt_compra >= r.dt_respondeu)
    / NULLIF(COUNT(DISTINCT r.nm_email), 0) * 100, 2
  )                                               AS taxa_conversao_pct

FROM respostas r
LEFT JOIN conversoes c USING (nm_email)
GROUP BY 1, 2
HAVING COUNT(DISTINCT r.nm_email) >= 20
ORDER BY nm_question, taxa_conversao_pct DESC;

-- -----------------------------------------------------------------------

-- 4c. Perfil completo: status × renda × resposta-chave × conversão
--     (substituir nm_question = '...' pela pergunta mais discriminante do 4b)
WITH

perfil AS (
  SELECT
    LOWER(TRIM(e.nm_email))                       AS nm_email,
    e.lead_status_at_registration,
    CASE
      WHEN e.cd_income_decile = -1  THEN '0_sem_dado'
      WHEN e.cd_income_decile <= 3  THEN '1_baixa'
      WHEN e.cd_income_decile <= 6  THEN '2_media'
      WHEN e.cd_income_decile <= 8  THEN '3_alta'
      WHEN e.cd_income_decile >= 9  THEN '4_top'
      ELSE '0_sem_dado'
    END                                           AS faixa_renda,
    s.nm_answer                                   AS resposta_chave,
    DATE(e.dt_registered_at)                      AS dt_registro
  FROM `bp-staging.dbt_abe.tb_leads_qualification_enriched` e
  LEFT JOIN `bp-staging.dbt_abe.tb_lead_surveys` s
    ON LOWER(TRIM(e.nm_email)) = LOWER(TRIM(s.nm_email))
    AND s.nm_campaign_tag = 'EVG'
    AND s.nm_question = 'SUBSTITUIR_PELA_PERGUNTA_CHAVE'  -- ajustar após ver resultado do 4b
  WHERE e.nm_campaign_tag = 'EVG'
),

conversoes AS (
  SELECT DISTINCT
    LOWER(TRIM(nm_email))                         AS nm_email
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_is_renovation = FALSE
    AND DATE(dt_ordered_at) >= '2026-05-23'
)

SELECT
  p.lead_status_at_registration,
  p.faixa_renda,
  COALESCE(p.resposta_chave, 'sem_resposta')      AS resposta_chave,
  COUNT(*)                                        AS leads,
  COUNTIF(c.nm_email IS NOT NULL)                 AS convertidos,
  ROUND(COUNTIF(c.nm_email IS NOT NULL) / NULLIF(COUNT(*), 0) * 100, 2)
                                                  AS taxa_conversao_pct
FROM perfil p
LEFT JOIN conversoes c USING (nm_email)
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 15
ORDER BY taxa_conversao_pct DESC;
