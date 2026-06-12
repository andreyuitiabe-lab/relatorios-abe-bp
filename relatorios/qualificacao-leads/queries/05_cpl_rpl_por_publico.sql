-- CPL atual vs RPL por campaign_name e ad_set_name
-- Referência: CPL atual médio = R$3,00
-- Pergunta: qual público justifica pagar mais? Qual está caro?
--
-- ⚠️ Janela curta (EVG = ~17 dias): RPL real está subestimado para Não Membros.
--    Usar coluna `proxy_decil7plus_pct` como indicador antecipado de qualidade.
--
-- ⚠️ ANTES DE RODAR: confirmar nomes de colunas UTM em lead_registration
--    via 01_explorar_schema.sql. Ajustar CTE `registros` se necessário.

DECLARE cpl_referencia FLOAT64 DEFAULT 3.00;

WITH

-- Leads com UTMs de origem (ad set / campaign)
-- ⚠️ Ajustar nomes de colunas UTM conforme schema real de lead_registration
registros AS (
  SELECT
    LOWER(TRIM(nm_email))                         AS nm_email,
    DATE(dt_created_at)                           AS dt_registro,

    -- Ajustar conforme resultado do 01_explorar_schema.sql:
    COALESCE(nm_campaign_name, utm_campaign)      AS nm_campaign_name,
    COALESCE(nm_ad_set_name,   utm_term)          AS nm_ad_set_name

  FROM `bp-lake.marketing.lead_registration`
  WHERE DATE(dt_created_at) >= '2026-05-01'
    AND COALESCE(nm_campaign_name, utm_campaign) IS NOT NULL
),

-- Enriquecimento: status + proxy de renda (decil7+)
leads_enriquecidos AS (
  SELECT
    LOWER(TRIM(nm_email))                         AS nm_email,
    lead_status_at_registration,
    cd_income_decile
  FROM `bp-staging.dbt_abe.tb_leads_qualification_enriched`
  WHERE nm_campaign_tag = 'EVG'
),

-- Investimento por ad set (Meta Ads)
investimento AS (
  SELECT
    nm_campaign_name,
    nm_ad_set_name,
    SUM(vl_amount_spent)                          AS investimento_total
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE DATE(reference_date) >= '2026-05-01'
    AND nm_campaign_name IS NOT NULL
    AND nm_ad_set_name IS NOT NULL
  GROUP BY 1, 2
),

-- Conversões pós-registro (email match)
conversoes AS (
  SELECT
    LOWER(TRIM(nm_email))                         AS nm_email,
    SUM(vl_payment_gross)                         AS receita
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_is_renovation = FALSE
    AND DATE(dt_ordered_at) >= '2026-05-23'      -- início EVG
  GROUP BY 1
),

-- Base por lead
base AS (
  SELECT
    r.nm_campaign_name,
    r.nm_ad_set_name,
    r.nm_email,
    r.dt_registro,
    e.lead_status_at_registration,
    e.cd_income_decile,
    COALESCE(c.receita, 0)                        AS receita
  FROM registros r
  LEFT JOIN leads_enriquecidos e USING (nm_email)
  LEFT JOIN conversoes c USING (nm_email)
)

SELECT
  b.nm_campaign_name,
  b.nm_ad_set_name,

  -- Volume e investimento
  COUNT(*)                                        AS total_leads,
  MAX(i.investimento_total)                       AS investimento_r$,

  -- CPL atual
  ROUND(MAX(i.investimento_total) / NULLIF(COUNT(*), 0), 2)
                                                  AS cpl_atual_r$,

  -- Mix de status (indicador de qualidade da audiência)
  ROUND(COUNTIF(b.lead_status_at_registration = 'Membro')
    / NULLIF(COUNT(*), 0) * 100, 1)              AS pct_membro,
  ROUND(COUNTIF(b.lead_status_at_registration = 'Ex-Membro')
    / NULLIF(COUNT(*), 0) * 100, 1)              AS pct_ex_membro,
  ROUND(COUNTIF(b.lead_status_at_registration = 'Não Membro')
    / NULLIF(COUNT(*), 0) * 100, 1)              AS pct_nao_membro,

  -- Proxy de qualidade de renda (% leads decil 7–10)
  -- Usar como indicador antecipado para Não Membros que ainda não converteram
  ROUND(COUNTIF(b.cd_income_decile >= 7 AND b.cd_income_decile != -1)
    / NULLIF(COUNTIF(b.cd_income_decile IS NOT NULL AND b.cd_income_decile != -1), 0) * 100, 1)
                                                  AS proxy_decil7plus_pct,

  -- Conversão e receita (atual — subestimada para Não Membros)
  COUNTIF(b.receita > 0)                          AS convertidos,
  ROUND(COUNTIF(b.receita > 0) / NULLIF(COUNT(*), 0) * 100, 2)
                                                  AS taxa_conversao_pct,
  ROUND(SUM(b.receita), 0)                        AS receita_total_r$,

  -- RPL = receita por lead gerado (medido até hoje)
  ROUND(SUM(b.receita) / NULLIF(COUNT(*), 0), 2) AS rpl_atual_r$,

  -- Decisão: CPL ideal é o RPL. Comparado com referência R$3,00.
  -- Positivo = CPL atual abaixo do RPL → pode pagar mais
  -- Negativo = CPL atual acima do RPL → está caro
  ROUND(
    SUM(b.receita) / NULLIF(COUNT(*), 0)
    - MAX(i.investimento_total) / NULLIF(COUNT(*), 0)
  , 2)                                            AS folga_cpl_r$,

  -- Flag de decisão vs referência R$3,00
  CASE
    WHEN SUM(b.receita) / NULLIF(COUNT(*), 0) > cpl_referencia * 2
      THEN 'escalar — RPL >> referência'
    WHEN SUM(b.receita) / NULLIF(COUNT(*), 0) > cpl_referencia
      THEN 'pode pagar mais'
    WHEN SUM(b.receita) / NULLIF(COUNT(*), 0) BETWEEN cpl_referencia * 0.7 AND cpl_referencia
      THEN 'no limite — monitorar'
    WHEN SUM(b.receita) / NULLIF(COUNT(*), 0) < cpl_referencia * 0.7
      AND COUNTIF(b.receita > 0) > 0
      THEN 'caro — reduzir CPL alvo'
    ELSE 'sem conversão ainda — usar proxy'
  END                                             AS decisao

FROM base b
LEFT JOIN investimento i
  ON b.nm_campaign_name = i.nm_campaign_name
  AND b.nm_ad_set_name = i.nm_ad_set_name

GROUP BY 1, 2
HAVING COUNT(*) >= 30          -- mínimo de amostra para estabilidade

ORDER BY
  -- Priorizar onde temos sinal claro (conversão) antes de sem-sinal
  COUNTIF(b.receita > 0) DESC,
  rpl_atual_r$ DESC;
