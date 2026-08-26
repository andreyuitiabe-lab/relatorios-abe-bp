-- Resumo da campanha (uma linha): leads, spend [LEAD] blendado, CPL, qualidade,
-- RPL projetado (cbo_campaign_rpl_estimate) e receita observada.
-- Parâmetros substituídos pelo refresh.py: tag e dt_inicio (tags reusadas, ex. JOM).
DECLARE tag STRING DEFAULT 'ENE';
DECLARE dt_inicio DATE DEFAULT '2026-07-27';

WITH leads AS (
    SELECT
        nm_iql_band, qt_iql_points, vl_reference_ev, vl_capi_event_value,
        ARRAY_LENGTH(arr_survey_responses) > 0 AS bl_resp, qt_vendas,
        (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) AS t
         WHERE t.vl_payment_gross IS NOT NULL AND t.days_to_purchase >= 0) AS vl_receita,
        (SELECT COUNT(*) FROM UNNEST(arr_st_approved_transactions) AS t
         WHERE t.vl_payment_gross IS NOT NULL AND t.days_to_purchase >= 0) AS qt_tx
    FROM `bp-datawarehouse.datamart.cbo_lead_conversion_iql`
    WHERE nm_tag = tag AND DATE(dt_registered_at_br) >= dt_inicio
),

spend AS (  -- todo spend [LEAD] cuja sigla (2º colchete) = tag, Meta + Google + PMax
    SELECT SUM(vl_amount_spent) AS vl_spend, MIN(reference_date) AS dt_spend_ini, MAX(reference_date) AS dt_spend_fim
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
),

proj AS (
    SELECT nm_estimator, vl_rpl_projected, vl_rpl_projected_lo, vl_rpl_projected_hi,
           pc_error_estimated, bl_capi_value_eligible, vl_campaign_factor, dt_reference
    FROM `bp-datawarehouse.datamart.cbo_campaign_rpl_estimate`
    WHERE nm_tag = tag
)

SELECT
    tag AS nm_tag,
    COUNT(*) AS qt_leads,
    s.vl_spend, s.dt_spend_ini, s.dt_spend_fim,
    ROUND(SAFE_DIVIDE(s.vl_spend, COUNT(*)), 2) AS vl_cpl,
    ROUND(100 * COUNTIF(l.nm_iql_band IN ('A+', 'A')) / COUNT(*), 1) AS pc_qual,
    COUNTIF(l.nm_iql_band IN ('A+', 'A')) AS qt_qual,
    ROUND(AVG(l.qt_iql_points), 1) AS vl_score,
    ROUND(AVG(l.vl_reference_ev), 2) AS vl_ev,
    ROUND(AVG(l.vl_capi_event_value), 2) AS vl_ev_capi,
    ROUND(100 * COUNTIF(l.bl_resp) / COUNT(*), 1) AS pc_survey,
    COUNTIF(l.bl_resp) AS qt_resp,
    ROUND(SAFE_DIVIDE(100 * COUNTIF(l.bl_resp AND l.nm_iql_band IN ('A+', 'A')),
                      COUNTIF(l.bl_resp)), 1) AS pc_qual_resp,
    ROUND(AVG(IF(l.bl_resp, l.vl_capi_event_value, NULL)), 2) AS vl_ev_capi_resp,
    ROUND(SUM(IFNULL(l.vl_receita, 0)), 0) AS vl_receita_obs,
    SUM(IFNULL(l.qt_tx, 0)) AS qt_vendas,
    COUNTIF(l.qt_vendas > 0) AS qt_compradores,
    p.nm_estimator, p.vl_rpl_projected, p.vl_rpl_projected_lo, p.vl_rpl_projected_hi,
    p.pc_error_estimated, p.bl_capi_value_eligible, p.vl_campaign_factor, p.dt_reference
FROM leads AS l
CROSS JOIN spend AS s
LEFT JOIN proj AS p ON TRUE
GROUP BY s.vl_spend, s.dt_spend_ini, s.dt_spend_fim, p.nm_estimator, p.vl_rpl_projected,
         p.vl_rpl_projected_lo, p.vl_rpl_projected_hi, p.pc_error_estimated,
         p.bl_capi_value_eligible, p.vl_campaign_factor, p.dt_reference
