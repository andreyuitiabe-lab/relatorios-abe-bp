-- Série diária por braço de teste (JOM) — leads, gasto, CPL, qualidade e retorno esperado.
--
-- Braço = campanha de captação da tag JOM. A JOM roda em TRÊS contas de mídia (Meta, Google
-- Ads e PMax) — a atribuição de cada uma está documentada em queries/_atribuicao.md.
-- ⚠️ Braços de FORM NATIVO ficam de fora da série: a ingestão é em lote e
--    dt_registered_at_br = hora do import, não do cadastro (a série seria fictícia).
--    Eles aparecem só no agregado (resumo_bracos.sql).
DECLARE dt_inicio DATE DEFAULT '2026-07-25';

WITH leads AS (
    SELECT
        DATE(i.dt_registered_at_br) AS dt_lead,
        i.nm_iql_band,
        i.qt_iql_points,
        i.vl_reference_ev,
        i.nm_survey_response_level,
        LOWER(i.utm_source) AS utm_source,
        REGEXP_EXTRACT(i.utm_content, r'(\d{10,})$') AS id_ad
    FROM `bp-datawarehouse.masterdata.fct_lead_iql` AS i
    WHERE i.nm_tag = 'JOM'
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

leads_dia AS (
    SELECT
        l.dt_lead,
        CASE
            WHEN a.nm_campaign_name IS NOT NULL
                THEN REGEXP_REPLACE(a.nm_campaign_name,
                    r'^\[LAN\] \[JOM[^\]]*\] \[LEAD\] (\[ADVANTAGE\] )?', '')
            WHEN l.utm_source = 'pmax' THEN 'Google PMax [PMAX]'
            WHEN l.utm_source = 'google' THEN 'Google Ads [KW]'
        END AS nm_arm,
        COUNT(*) AS qt_leads,
        COUNTIF(l.nm_iql_band IN ('A+', 'A')) AS qt_qual,
        AVG(l.qt_iql_points) AS vl_score,
        AVG(l.vl_reference_ev) AS vl_ev,
        COUNTIF(l.nm_survey_response_level = 'sim') AS qt_resp
    FROM leads AS l
    LEFT JOIN ads AS a USING (id_ad)
    GROUP BY 1, 2
    HAVING nm_arm IS NOT NULL
),

spend_dia AS (  -- gasto diário das três contas, no mesmo rótulo de braço
    SELECT
        reference_date AS dt_lead,
        REGEXP_REPLACE(nm_campaign_name,
            r'^\[LAN\] \[JOM[^\]]*\] \[LEAD\] (\[ADVANTAGE\] )?', '') AS nm_arm,
        SUM(vl_amount_spent) AS vl_spend
    FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
    WHERE nm_campaign_name LIKE '%JOM%'
      AND nm_campaign_name NOT LIKE '%JOM-FORM%'
      AND reference_date >= dt_inicio
    GROUP BY 1, 2
    UNION ALL
    SELECT reference_date, 'Google PMax [PMAX]', SUM(vl_amount_spent)
    FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
    WHERE nm_campaign_name LIKE '%[JOM]%' AND nm_campaign_name LIKE '%[LEAD]%'
      AND reference_date >= dt_inicio
    GROUP BY 1, 2
    UNION ALL
    SELECT reference_date, 'Google Ads [KW]', SUM(vl_amount_spent)
    FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
    WHERE nm_campaign_name LIKE '%[JOM]%' AND nm_campaign_name LIKE '%[LEAD]%'
      AND reference_date >= dt_inicio
    GROUP BY 1, 2
),

final AS (
    SELECT
        FORMAT_DATE('%d/%m', l.dt_lead) AS dt_label,
        l.dt_lead,
        l.nm_arm,
        l.qt_leads,
        ROUND(s.vl_spend, 2) AS vl_spend,
        ROUND(SAFE_DIVIDE(s.vl_spend, l.qt_leads), 2) AS vl_cpl,
        ROUND(100 * l.qt_qual / l.qt_leads, 1) AS pc_qual,
        ROUND(l.vl_score, 1) AS vl_score,
        ROUND(SAFE_DIVIDE(l.vl_ev * l.qt_leads, s.vl_spend), 2) AS vl_retorno_esp,
        ROUND(100 * l.qt_resp / l.qt_leads, 1) AS pc_survey
    FROM leads_dia AS l
    LEFT JOIN spend_dia AS s USING (dt_lead, nm_arm)
)

SELECT * FROM final ORDER BY dt_lead, nm_arm
