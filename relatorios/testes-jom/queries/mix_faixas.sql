-- Mix de faixas IQL por braço de teste (JOM) — geral e entre respondentes
--
-- A comparação de qualidade entre braços com cobertura de pesquisa diferente só é
-- justa entre respondentes: sem pesquisa, o lead cai para as faixas baixas por
-- ausência de sinal, não por ser pior (medido no JOM-FORM: score −18,3 geral vs
-- −3,4 entre respondentes, idêntico ao braço padrão).
DECLARE dt_inicio DATE DEFAULT '2026-07-25';

WITH leads AS (
    SELECT
        i.nm_tag,
        i.nm_iql_band,
        i.nm_survey_response_level,
        REGEXP_EXTRACT(i.utm_content, r'(\d{10,})$') AS id_ad
    FROM `bp-datawarehouse.masterdata.fct_lead_iql` AS i
    WHERE i.nm_tag LIKE 'JOM%' AND DATE(i.dt_registered_at_br) >= dt_inicio
),

ads AS (
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
            WHEN l.nm_tag LIKE '%FORMS' THEN 'Form nativo Meta'
            WHEN a.nm_campaign_name IS NOT NULL
                THEN REGEXP_REPLACE(a.nm_campaign_name, r'^\[LAN\] \[JOM[^\]]*\] \[LEAD\] ', '')
            ELSE 'Sem atribuição (orgânico/CRM/UTM ausente)'
        END AS nm_arm,
        l.nm_iql_band,
        COUNT(*) AS qt_leads,
        COUNTIF(l.nm_survey_response_level = 'sim') AS qt_resp
    FROM leads AS l
    LEFT JOIN ads AS a USING (id_ad)
    GROUP BY 1, 2
)

SELECT * FROM final ORDER BY nm_arm, nm_iql_band
