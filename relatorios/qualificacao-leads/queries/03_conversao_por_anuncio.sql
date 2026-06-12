-- PASSO 3: Conversão e RPL por anúncio / ad set / campanha
-- Objetivo: identificar quais criativos trazem leads de maior qualidade (maior tx. conversão e RPL)
-- Método: join lead_registration (UTMs) → enriquecimento → conversão → Meta Ads (investimento)
--
-- ⚠️ ATENÇÃO DE SCHEMA: se lead_registration tiver colunas com nomes diferentes,
--    ajustar os aliases na CTE `registros`. Rodar 01_explorar_schema.sql primeiro.
--
-- Assumindo que lead_registration tem:
--   nm_email, dt_created_at, utm_campaign, utm_content (ad_id), utm_term ou utm_source,
--   e possivelmente nm_campaign_name, nm_ad_set_name, nm_ad_name diretamente

WITH

-- Registros de leads com UTMs
registros AS (
  SELECT
    LOWER(TRIM(nm_email))                         AS nm_email,
    DATE(dt_created_at)                           AS dt_registro,

    -- ⚠️ Ajustar nomes de colunas conforme resultado do 01_explorar_schema.sql
    COALESCE(nm_campaign_name, utm_campaign)      AS nm_campaign_name,
    COALESCE(nm_ad_set_name,   utm_term)          AS nm_ad_set_name,
    COALESCE(nm_ad_name,       utm_content)       AS nm_ad_name_raw,

    -- Extrai ID do anúncio do utm_content (padrão BP: ...__12345)
    REGEXP_EXTRACT(
      COALESCE(nm_ad_name, utm_content),
      r'__(\d+)$'
    )                                             AS id_ad_extraido

  FROM `bp-lake.marketing.lead_registration`
  WHERE DATE(dt_created_at) >= '2026-05-01'  -- EVG + contexto recente
),

-- Enriquecimento: status e renda do lead
leads_enriquecidos AS (
  SELECT
    LOWER(TRIM(nm_email))                         AS nm_email,
    nm_campaign_tag,
    lead_status_at_registration,
    CASE
      WHEN cd_income_decile = -1  THEN '0_sem_dado'
      WHEN cd_income_decile <= 3  THEN '1_baixa'
      WHEN cd_income_decile <= 6  THEN '2_media'
      WHEN cd_income_decile <= 8  THEN '3_alta'
      WHEN cd_income_decile >= 9  THEN '4_top'
      ELSE '0_sem_dado'
    END                                           AS faixa_renda,
    cd_income_decile
  FROM `bp-staging.dbt_abe.tb_leads_qualification_enriched`
  WHERE nm_campaign_tag IN ('EVG', 'DOM', 'DBI')
),

-- Conversões pós-registro
conversoes AS (
  SELECT DISTINCT
    LOWER(TRIM(nm_email))                         AS nm_email,
    MIN(DATE(dt_ordered_at))                      AS dt_primeira_compra,
    SUM(vl_payment_gross)                         AS receita_total
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_is_renovation = FALSE
    AND DATE(dt_ordered_at) >= '2026-05-01'
  GROUP BY 1
),

-- Investimento por anúncio (Meta Ads)
investimento_meta AS (
  SELECT
    nm_campaign_name,
    nm_ad_set_name,
    nm_ad_name,
    CAST(id_advertising AS STRING)                AS id_advertising,
    SUM(vl_amount_spent)                          AS investimento_total
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE DATE(reference_date) >= '2026-05-01'
  GROUP BY 1, 2, 3, 4
),

-- Base consolidada por lead
base AS (
  SELECT
    r.nm_campaign_name,
    r.nm_ad_set_name,
    r.nm_ad_name_raw,
    r.id_ad_extraido,
    l.nm_campaign_tag,
    l.lead_status_at_registration,
    l.faixa_renda,
    r.nm_email,
    c.nm_email IS NOT NULL
      AND c.dt_primeira_compra >= r.dt_registro   AS bl_converteu,
    COALESCE(c.receita_total, 0)                  AS receita
  FROM registros r
  LEFT JOIN leads_enriquecidos l USING (nm_email)
  LEFT JOIN conversoes c USING (nm_email)
)

SELECT
  b.nm_campaign_name,
  b.nm_ad_set_name,
  -- Prefere nome do anúncio da Meta Ads (mais legível que utm_content bruto)
  COALESCE(m.nm_ad_name, b.nm_ad_name_raw)        AS nm_ad_name,
  b.lead_status_at_registration,
  b.faixa_renda,

  COUNT(*)                                        AS total_leads,
  COUNTIF(b.bl_converteu)                         AS convertidos,
  ROUND(COUNTIF(b.bl_converteu) / NULLIF(COUNT(*), 0) * 100, 2)
                                                  AS taxa_conversao_pct,

  ROUND(SUM(b.receita) / NULLIF(COUNT(*), 0), 2) AS rpl,  -- R$ receita por lead

  -- CPL ideal = RPL (teto para break-even sem margem)
  -- Multiplicar por fator de margem para obter CPL alvo real:
  -- ex: RPL × 0.5 → CPL que gera 50% de margem bruta
  ROUND(SUM(b.receita) / NULLIF(COUNT(*), 0), 2) AS cpl_ideal_teto,

  MAX(m.investimento_total)                       AS investimento_meta,
  ROUND(
    MAX(m.investimento_total) / NULLIF(COUNT(*), 0), 2
  )                                               AS cpl_atual

FROM base b
LEFT JOIN investimento_meta m
  ON b.id_ad_extraido = m.id_advertising

WHERE b.nm_campaign_name IS NOT NULL

GROUP BY 1, 2, 3, 4, 5
HAVING COUNT(*) >= 20

ORDER BY
  rpl DESC,
  taxa_conversao_pct DESC;
