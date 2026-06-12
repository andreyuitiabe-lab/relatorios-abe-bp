-- PASSO 1: Exploração de schema
-- Rodar antes das demais queries para confirmar nomes de colunas
-- nas tabelas que ainda não temos schema documentado

-- 1a. Colunas de lead_registration (fonte dos UTMs de ad/ad_set/campaign)
SELECT column_name, data_type
FROM `bp-lake.marketing.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'lead_registration'
ORDER BY ordinal_position;

-- -----------------------------------------------------------------------

-- 1b. Colunas de tb_leads_qualification_enriched (confirmar campos disponíveis)
SELECT column_name, data_type
FROM `bp-staging.dbt_abe.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'tb_leads_qualification_enriched'
ORDER BY ordinal_position;

-- -----------------------------------------------------------------------

-- 1c. Colunas de tb_lead_surveys (confirmar se EVG está coberta)
SELECT column_name, data_type
FROM `bp-staging.dbt_abe.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'tb_lead_surveys'
ORDER BY ordinal_position;

-- -----------------------------------------------------------------------

-- 1d. Campanhas e counts em tb_leads_qualification_enriched (confirmar EVG está lá)
SELECT
  nm_campaign_tag,
  COUNT(*)                                      AS total_leads,
  MIN(DATE(dt_registered_at))                   AS primeiro_lead,
  MAX(DATE(dt_registered_at))                   AS ultimo_lead
FROM `bp-staging.dbt_abe.tb_leads_qualification_enriched`
GROUP BY 1
ORDER BY ultimo_lead DESC
LIMIT 20;

-- -----------------------------------------------------------------------

-- 1e. Sample de tb_lead_surveys para EVG (se existir)
SELECT *
FROM `bp-staging.dbt_abe.tb_lead_surveys`
WHERE nm_campaign_tag = 'EVG'
  OR nm_campaign_tag LIKE '%evg%'
  OR nm_campaign_tag LIKE '%evan%'
LIMIT 20;
