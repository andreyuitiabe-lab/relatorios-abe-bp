-- Mix de faixas IQL por braço de teste (JOM) — geral e entre respondentes
--
-- Braço = campanha de captação da tag JOM. A JOM roda em TRÊS contas de mídia (Meta, Google
-- Ads e PMax) — a atribuição de cada uma está documentada em queries/_atribuicao.md.
-- ⚠️ Olhar só o facebook_ads_funnel joga ~941 leads/semana de Google e PMax no balde
--    "sem atribuição", lidos como orgânico. Sempre unir as três tabelas de funil.
--
-- A comparação de qualidade entre braços com cobertura de pesquisa diferente só é justa
-- entre respondentes: sem pesquisa o lead cai nas faixas baixas por ausência de sinal.
-- ⚠️ Mix com zero em B e zero em D é assinatura de score SEM pesquisa, não de público ruim
--    (caso do form nativo desde 28/08/2026 — ver ANALISE.md).
DECLARE dt_inicio DATE DEFAULT '2026-07-25';

WITH leads AS (
    SELECT
        i.nm_tag,
        i.nm_iql_band,
        i.nm_survey_response_level,
        LOWER(i.utm_source) AS utm_source,
        REGEXP_EXTRACT(i.utm_content, r'(\d{10,})$') AS id_ad
    FROM `bp-datawarehouse.masterdata.fct_lead_iql` AS i
    WHERE i.nm_tag IN ('JOM', 'JOM-BR-FORMS')
      AND DATE(i.dt_registered_at_br) >= dt_inicio
),

ads AS (  -- id do anúncio Meta -> campanha
    SELECT
        CAST(id_advertising AS STRING) AS id_ad,
        ANY_VALUE(nm_campaign_name) AS nm_campaign_name
    FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
    WHERE nm_campaign_name LIKE '%JOM%' AND reference_date >= dt_inicio
    GROUP BY 1
),

final AS (
    SELECT
        CASE
            WHEN l.nm_tag LIKE '%FORMS' THEN 'Form nativo (Meta)'
            WHEN a.nm_campaign_name IS NOT NULL
                THEN REGEXP_REPLACE(a.nm_campaign_name,
                    r'^\[LAN\] \[JOM[^\]]*\] \[LEAD\] (\[ADVANTAGE\] )?', '')
            WHEN l.utm_source = 'pmax' THEN 'Google PMax [PMAX]'
            WHEN l.utm_source = 'google' THEN 'Google Ads [KW]'
            ELSE 'Sem atribuição (orgânico/CRM)'
        END AS nm_arm,
        l.nm_iql_band,
        COUNT(*) AS qt_leads,
        COUNTIF(l.nm_survey_response_level = 'sim') AS qt_resp
    FROM leads AS l
    LEFT JOIN ads AS a USING (id_ad)
    GROUP BY 1, 2
)

SELECT * FROM final ORDER BY nm_arm, nm_iql_band
