-- Resumo agregado survey vs base, EXCLUINDO dias anômalos de CTR colapsado (ex: BP10 em 26-27/jun)
WITH meta AS (
      SELECT id_advertising, ANY_VALUE(nm_campaign_name) AS nm_campaign_name, SUM(vl_amount_spent) AS spent
      FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
      WHERE reference_date >= '2026-06-19' AND reference_date NOT IN ('2026-06-26', '2026-06-27') AND nm_campaign_name LIKE '%[BP10]%[LEAD]%'
      GROUP BY id_advertising
    ),
    leads AS (
      SELECT REGEXP_EXTRACT(utm_content, r'([0-9]+)$') AS id_advertising,
        COUNT(*) AS qt_leads,
        COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) AS qt_resp,
        COUNTIF(EXISTS(SELECT 1 FROM UNNEST(arr_st_approved_transactions) t
                       WHERE t.days_to_purchase BETWEEN 0 AND 30)) AS qt_comprou
      FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
      WHERE dt_registered_at_br >= '2026-06-19' AND DATE(dt_registered_at_br) NOT IN ('2026-06-26', '2026-06-27') AND utm_medium = 'facebook_ads'
      GROUP BY 1
    )
    SELECT
      CASE WHEN m.nm_campaign_name LIKE '%Survey%' THEN 'survey' ELSE 'base' END AS grupo,
      ROUND(SUM(m.spent), 0) AS invest, SUM(l.qt_leads) AS leads,
      ROUND(SUM(m.spent) / NULLIF(SUM(l.qt_leads), 0), 2) AS cpl,
      ROUND(SUM(l.qt_resp) / NULLIF(SUM(l.qt_leads), 0) * 100, 1) AS taxa_resp,
      ROUND(SUM(m.spent) / NULLIF(SUM(l.qt_resp), 0), 2) AS custo_resp,
      ROUND(SUM(l.qt_comprou) / NULLIF(SUM(l.qt_leads), 0) * 100, 2) AS conv_pct
    FROM meta m LEFT JOIN leads l USING (id_advertising)
    GROUP BY 1 ORDER BY 1
