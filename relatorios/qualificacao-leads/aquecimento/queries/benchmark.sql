-- Benchmark entre campanhas: retorno projetado (RPL do projetor ÷ CPL blendado [LEAD]).
-- Só tags com spend [LEAD] desde 2025-08-01 (spend Meta indisponível antes) e ≥ 5k leads.
WITH spend AS (
    SELECT REGEXP_EXTRACT(nm_campaign_name, r'^\[[A-Z0-9]+\]\s*\[([A-Z0-9-]+)\]') AS nm_tag,
           SUM(vl_amount_spent) AS vl_spend, MIN(reference_date) AS dt_ini, MAX(reference_date) AS dt_fim
    FROM (
        SELECT nm_campaign_name, reference_date, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
        UNION ALL
        SELECT nm_campaign_name, reference_date, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
        UNION ALL
        SELECT nm_campaign_name, reference_date, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
    )
    WHERE REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lead\]') AND vl_amount_spent > 0
      AND reference_date >= '2025-08-01'
    GROUP BY 1
),

leads AS (
    SELECT nm_tag, COUNT(*) AS qt_leads,
           ROUND(100 * COUNTIF(nm_iql_band IN ('A+', 'A')) / COUNT(*), 1) AS pc_qual,
           ROUND(100 * COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) / COUNT(*), 1) AS pc_survey,
           MIN(DATE(dt_registered_at_br)) AS dt_lead_ini
    FROM `bp-datawarehouse.datamart.cbo_lead_conversion_iql`
    WHERE DATE(dt_registered_at_br) >= '2025-08-01'
    GROUP BY 1
)

SELECT l.nm_tag, l.qt_leads, l.pc_qual, l.pc_survey, l.dt_lead_ini,
       ROUND(s.vl_spend, 0) AS vl_spend, s.dt_ini AS dt_spend_ini, s.dt_fim AS dt_spend_fim,
       ROUND(SAFE_DIVIDE(s.vl_spend, l.qt_leads), 2) AS vl_cpl,
       p.nm_estimator, p.vl_rpl_projected,
       ROUND(SAFE_DIVIDE(p.vl_rpl_projected * l.qt_leads, s.vl_spend), 2) AS vl_retorno_proj
FROM leads AS l
INNER JOIN spend AS s USING (nm_tag)
LEFT JOIN `bp-datawarehouse.datamart.cbo_campaign_rpl_estimate` AS p USING (nm_tag)
WHERE l.qt_leads >= 5000 AND s.vl_spend >= 5000
ORDER BY vl_retorno_proj DESC
