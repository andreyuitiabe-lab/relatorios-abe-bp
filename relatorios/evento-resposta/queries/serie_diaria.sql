-- Série diária CPL, custo/resposta e CTR: survey vs base (parametrizado; ex: EVG)
WITH ad_grupo AS (
      SELECT id_advertising,
        CASE WHEN ANY_VALUE(nm_campaign_name) LIKE '%Survey%' THEN 'survey' ELSE 'base' END AS grupo
      FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
      WHERE nm_campaign_name LIKE '%[EVG]%[LEAD]%' AND reference_date >= '2026-06-01'
      GROUP BY id_advertising
    ),
    spend_daily AS (
      SELECT f.reference_date AS dia, g.grupo,
        SUM(f.vl_amount_spent) AS spent,
        SUM(f.qt_outbound_clicks) AS clicks,
        SUM(f.qt_impressions) AS impr
      FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel` f
      JOIN ad_grupo g USING (id_advertising)
      WHERE f.reference_date >= '2026-06-19'
      GROUP BY 1, 2
    ),
    leads_daily AS (
      SELECT DATE(lc.dt_registered_at_br) AS dia, g.grupo,
        COUNT(*) AS leads,
        COUNTIF(ARRAY_LENGTH(lc.arr_survey_responses) > 0) AS resp
      FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion` lc
      JOIN ad_grupo g ON g.id_advertising = REGEXP_EXTRACT(lc.utm_content, r'([0-9]+)$')
      WHERE DATE(lc.dt_registered_at_br) >= '2026-06-19' AND lc.utm_medium = 'facebook_ads'
      GROUP BY 1, 2
    )
    SELECT CAST(dia AS STRING) AS dia, grupo,
      ROUND(spent / NULLIF(leads, 0), 2) AS cpl,
      ROUND(spent / NULLIF(resp, 0), 2) AS custo_resp,
      ROUND(clicks / NULLIF(impr, 0) * 100, 2) AS ctr
    FROM spend_daily FULL JOIN leads_daily USING (dia, grupo)
    ORDER BY dia, grupo
