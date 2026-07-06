-- Extração para Random Forest — feature importance da qualificação de leads
-- Escopo: Não Membros que responderam pesquisa (237k, ~5,3% conversão)
-- Alvo: conv = converteu em qualquer cadastro (bl_converted)
-- Unidade: 1 linha por email (dedup enriched pela linha mais recente; survey mais recente)

WITH nm AS (
  SELECT
    nm_email,
    MAX(bl_converted) AS conv,
    -- features de enriquecimento: pega da linha mais recente
    ARRAY_AGG(nm_tag           IGNORE NULLS ORDER BY dt_registered_at_br DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_tag,
    ARRAY_AGG(nm_lead_channel  IGNORE NULLS ORDER BY dt_registered_at_br DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_lead_channel,
    ARRAY_AGG(cd_uf            IGNORE NULLS ORDER BY dt_registered_at_br DESC LIMIT 1)[SAFE_OFFSET(0)] AS cd_uf,
    ARRAY_AGG(nm_region        IGNORE NULLS ORDER BY dt_registered_at_br DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_region,
    ARRAY_AGG(nm_city_size     IGNORE NULLS ORDER BY dt_registered_at_br DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_city_size,
    ARRAY_AGG(cd_income_decile IGNORE NULLS ORDER BY dt_registered_at_br DESC LIMIT 1)[SAFE_OFFSET(0)] AS cd_income_decile,
    ARRAY_AGG(nm_credit_card_level IGNORE NULLS ORDER BY dt_registered_at_br DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_credit_card_level,
    ARRAY_AGG(vl_idade         IGNORE NULLS ORDER BY dt_registered_at_br DESC LIMIT 1)[SAFE_OFFSET(0)] AS vl_idade_interno
  FROM `bp-staging.dbt_abe.tb_leads_qualification_enriched`
  WHERE status_lead = 'Não Membro'
  GROUP BY nm_email
),
sv AS (
  SELECT
    nm_email,
    ARRAY_AGG(survey_tag     ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS survey_tag,
    ARRAY_AGG(nm_idade       ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_idade,
    ARRAY_AGG(nm_genero      ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_genero,
    ARRAY_AGG(nm_estado_civil ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_estado_civil,
    ARRAY_AGG(nm_filhos      ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_filhos,
    ARRAY_AGG(nm_ocupacao    ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_ocupacao,
    ARRAY_AGG(nm_renda       ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_renda,
    ARRAY_AGG(nm_escolaridade ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_escolaridade,
    ARRAY_AGG(nm_conhece_bp  ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS nm_conhece_bp,
    ARRAY_AGG(vl_relevancia  ORDER BY ts_survey DESC LIMIT 1)[SAFE_OFFSET(0)] AS vl_relevancia
  FROM `bp-staging.dbt_abe.tb_lead_surveys`
  GROUP BY nm_email
)
SELECT
  nm.conv,
  nm.nm_tag, nm.nm_lead_channel, nm.cd_uf, nm.nm_region, nm.nm_city_size,
  nm.cd_income_decile, nm.nm_credit_card_level, nm.vl_idade_interno,
  sv.survey_tag, sv.nm_idade, sv.nm_genero, sv.nm_estado_civil, sv.nm_filhos,
  sv.nm_ocupacao, sv.nm_renda, sv.nm_escolaridade, sv.nm_conhece_bp, sv.vl_relevancia
FROM nm
INNER JOIN sv USING (nm_email)
