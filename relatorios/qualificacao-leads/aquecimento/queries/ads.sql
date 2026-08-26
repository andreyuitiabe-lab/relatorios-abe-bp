-- Qualidade por anúncio Meta (id extraído do utm_content — regex robusta, bq-leads.md).
-- Só anúncios com spend > 0 e leads > 0. n mínimo por criativo tratado na página (D16: 50).
DECLARE tag STRING DEFAULT 'ENE';
DECLARE dt_inicio DATE DEFAULT '2026-07-27';

WITH leads AS (
    SELECT
        REGEXP_EXTRACT(utm_content, r'(\d{10,})$') AS id_ad,
        nm_iql_band, qt_iql_points, vl_capi_event_value, ARRAY_LENGTH(arr_survey_responses) > 0 AS bl_resp, qt_vendas,
        (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) AS t
         WHERE t.vl_payment_gross IS NOT NULL AND t.days_to_purchase >= 0) AS vl_receita
    FROM `bp-datawarehouse.datamart.cbo_lead_conversion_iql`
    WHERE nm_tag = tag AND DATE(dt_registered_at_br) >= dt_inicio
),

ads AS (
    SELECT
        CAST(id_advertising AS STRING) AS id_ad,
        ANY_VALUE(nm_ad_name) AS nm_ad,
        ANY_VALUE(nm_ad_set_name) AS nm_adset,
        SUM(vl_amount_spent) AS vl_spend
    FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
    WHERE REGEXP_EXTRACT(nm_campaign_name, r'^\[[A-Z0-9]+\]\s*\[([A-Z0-9-]+)\]') = tag
      AND REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lead\]')
      AND reference_date >= dt_inicio
    GROUP BY 1
    HAVING vl_spend > 0
)

SELECT
    a.id_ad,
    REGEXP_REPLACE(a.nm_ad, r'\s*-\s*\[LAN\]\s*\[[A-Z0-9-]+\]\s*', ' — ') AS nm_ad,
    a.nm_adset,
    ROUND(a.vl_spend, 2) AS vl_spend,
    COUNT(l.id_ad) AS qt_leads,
    ROUND(SAFE_DIVIDE(a.vl_spend, COUNT(l.id_ad)), 2) AS vl_cpl,
    COUNTIF(l.nm_iql_band = 'A+') AS qt_a_plus,
    COUNTIF(l.nm_iql_band = 'A') AS qt_a,
    COUNTIF(l.nm_iql_band = 'B') AS qt_b,
    COUNTIF(l.nm_iql_band = 'C') AS qt_c,
    COUNTIF(l.nm_iql_band = 'D') AS qt_d,
    ROUND(AVG(l.qt_iql_points), 1) AS vl_score,
    ROUND(AVG(l.vl_capi_event_value), 2) AS vl_ev_capi,
    ROUND(100 * SAFE_DIVIDE(COUNTIF(l.bl_resp), COUNT(l.id_ad)), 1) AS pc_survey,
    ROUND(AVG(IF(l.bl_resp, l.vl_capi_event_value, NULL)), 2) AS vl_ev_capi_resp,
    ROUND(SAFE_DIVIDE(AVG(l.vl_capi_event_value) * COUNT(l.id_ad), a.vl_spend), 2) AS vl_retorno_esp,
    COUNTIF(l.qt_vendas > 0) AS qt_compradores,
    ROUND(SUM(IFNULL(l.vl_receita, 0)), 0) AS vl_receita_obs
FROM ads AS a
LEFT JOIN leads AS l USING (id_ad)
GROUP BY a.id_ad, a.nm_ad, a.nm_adset, a.vl_spend
HAVING qt_leads > 0
ORDER BY a.vl_spend DESC
