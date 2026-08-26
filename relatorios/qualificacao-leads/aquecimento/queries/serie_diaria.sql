-- Série diária da campanha: leads por faixa, spend [LEAD] blendado do dia, CPL,
-- RPL esperado do dia (média do valor CAPI = EV da faixa × fator da campanha) e retorno.
DECLARE tag STRING DEFAULT 'ENE';
DECLARE dt_inicio DATE DEFAULT '2026-07-27';

WITH leads AS (
    SELECT
        DATE(dt_registered_at_br) AS dt,
        COUNT(*) AS qt_leads,
        COUNTIF(nm_iql_band = 'A+') AS qt_a_plus,
        COUNTIF(nm_iql_band = 'A') AS qt_a,
        COUNTIF(nm_iql_band = 'B') AS qt_b,
        COUNTIF(nm_iql_band = 'C') AS qt_c,
        COUNTIF(nm_iql_band = 'D') AS qt_d,
        COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) AS qt_resp,
        AVG(vl_capi_event_value) AS vl_ev_capi,
        AVG(qt_iql_points) AS vl_score
    FROM `bp-datawarehouse.datamart.cbo_lead_conversion_iql`
    WHERE nm_tag = tag AND DATE(dt_registered_at_br) >= dt_inicio
    GROUP BY 1
),

spend AS (
    SELECT reference_date AS dt, SUM(vl_amount_spent) AS vl_spend
    FROM (
        SELECT nm_campaign_name, reference_date, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
        UNION ALL
        SELECT nm_campaign_name, reference_date, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
        UNION ALL
        SELECT nm_campaign_name, reference_date, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
    )
    WHERE REGEXP_EXTRACT(nm_campaign_name, r'^\[[A-Z0-9]+\]\s*\[([A-Z0-9-]+)\]') = tag
      AND REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lead\]')
      AND reference_date >= dt_inicio AND vl_amount_spent > 0
    GROUP BY 1
)

SELECT
    l.dt,
    l.qt_leads, l.qt_a_plus, l.qt_a, l.qt_b, l.qt_c, l.qt_d, l.qt_resp,
    ROUND(l.vl_score, 1) AS vl_score,
    ROUND(l.vl_ev_capi, 2) AS vl_ev_capi,
    ROUND(s.vl_spend, 2) AS vl_spend,
    ROUND(SAFE_DIVIDE(s.vl_spend, l.qt_leads), 2) AS vl_cpl,
    ROUND(SAFE_DIVIDE(l.vl_ev_capi * l.qt_leads, s.vl_spend), 2) AS vl_retorno_esp
FROM leads AS l
LEFT JOIN spend AS s USING (dt)
ORDER BY l.dt
