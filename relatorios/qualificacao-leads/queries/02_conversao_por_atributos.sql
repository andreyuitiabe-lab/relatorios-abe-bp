-- PASSO 2: Conversão por atributos do lead
-- Objetivo: identificar quais combinações status × renda × pesquisa têm maior lift de conversão
-- Campanhas: EVG + histórico recente para referência
-- ⚠️ EVG iniciou ~23/05/2026 — janela curta. Não Membros têm janela de ~421 dias.
--    Para EVG, maioria das conversões registradas serão de Membros (convertem rápido).

WITH

leads AS (
  SELECT
    l.nm_email,
    l.nm_campaign_tag,
    l.lead_status_at_registration,

    -- Renda em faixas (decil -1 = CEP sem cobertura)
    CASE
      WHEN l.cd_income_decile = -1   THEN '0_sem_dado'
      WHEN l.cd_income_decile <= 3   THEN '1_baixa (D1-3)'
      WHEN l.cd_income_decile <= 6   THEN '2_media (D4-6)'
      WHEN l.cd_income_decile <= 8   THEN '3_alta (D7-8)'
      WHEN l.cd_income_decile >= 9   THEN '4_top (D9-10)'
      ELSE '0_sem_dado'
    END                                           AS faixa_renda,

    l.cd_income_decile,
    l.id_user IS NOT NULL                         AS bl_tem_dados_internos,
    DATE(l.dt_registered_at)                      AS dt_registro

  FROM `bp-staging.dbt_abe.tb_leads_qualification_enriched` l
  WHERE l.nm_campaign_tag IS NOT NULL
    AND l.nm_campaign_tag IN ('EVG', 'DOM', 'DBI', 'VDS')  -- últimas campanhas para referência
),

-- Conversões: qualquer compra aprovada, não-renovação, pelo email do lead
-- Atribuição ampla (não restrita a UTM da campanha) para capturar conversões tardias
conversoes AS (
  SELECT DISTINCT
    LOWER(TRIM(nm_email))                         AS nm_email,
    MIN(DATE(dt_ordered_at))                      AS dt_primeira_compra
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_is_renovation = FALSE
  GROUP BY 1
),

-- Respostas de formulário/pesquisa (se disponível por campanha)
pesquisas AS (
  SELECT
    LOWER(TRIM(nm_email))                         AS nm_email,
    nm_campaign_tag,
    COUNT(*)                                      AS qt_respostas
  FROM `bp-staging.dbt_abe.tb_lead_surveys`
  GROUP BY 1, 2
)

SELECT
  l.nm_campaign_tag,
  l.lead_status_at_registration,
  l.faixa_renda,
  l.bl_tem_dados_internos,
  p.qt_respostas IS NOT NULL                      AS bl_respondeu_pesquisa,

  COUNT(*)                                        AS total_leads,
  COUNTIF(c.nm_email IS NOT NULL
    AND c.dt_primeira_compra >= l.dt_registro)    AS convertidos,

  ROUND(
    COUNTIF(c.nm_email IS NOT NULL
      AND c.dt_primeira_compra >= l.dt_registro)
    / NULLIF(COUNT(*), 0) * 100, 2
  )                                               AS taxa_conversao_pct,

  ROUND(AVG(l.cd_income_decile) IGNORE NULLS, 1) AS decil_medio

FROM leads l
LEFT JOIN conversoes c
  ON LOWER(TRIM(l.nm_email)) = c.nm_email
LEFT JOIN pesquisas p
  ON LOWER(TRIM(l.nm_email)) = p.nm_email
  AND l.nm_campaign_tag = p.nm_campaign_tag

GROUP BY 1, 2, 3, 4, 5

-- Filtro mínimo de amostra para estabilidade estatística
HAVING COUNT(*) >= 30

ORDER BY
  l.nm_campaign_tag,
  taxa_conversao_pct DESC;
