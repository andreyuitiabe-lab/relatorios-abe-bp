WITH meta AS (
  SELECT id_advertising,
    REGEXP_EXTRACT(ANY_VALUE(nm_campaign_name), r'\[([A-Z0-9]+)\] \[LEAD\]') AS lancamento,
    SUM(vl_amount_spent) AS spent
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 120 DAY)
    AND nm_campaign_name LIKE '%[LEAD]%'
  GROUP BY id_advertising
),
leads AS (
  SELECT REGEXP_EXTRACT(utm_content, r'([0-9]+)$') AS id_advertising,
    COUNT(*) AS qt_leads,
    COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) AS qt_resp,
    COUNTIF(EXISTS(SELECT 1 FROM UNNEST(arr_st_approved_transactions) t
                   WHERE t.days_to_purchase BETWEEN 0 AND 30)) AS qt_comprou
  FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
  WHERE dt_registered_at_br >= DATE_SUB(CURRENT_DATE(), INTERVAL 120 DAY)
    AND utm_medium = 'facebook_ads'
  GROUP BY 1
)
SELECT m.lancamento,
  ROUND(SUM(m.spent), 0) AS invest, SUM(l.qt_leads) AS leads,
  ROUND(SUM(m.spent) / NULLIF(SUM(l.qt_leads), 0), 2) AS cpl,
  ROUND(SUM(l.qt_resp) / NULLIF(SUM(l.qt_leads), 0) * 100, 1) AS taxa_resp,
  ROUND(SUM(l.qt_comprou) / NULLIF(SUM(l.qt_leads), 0) * 100, 2) AS conv_pct,
  ROUND(SUM(m.spent) / NULLIF(SUM(l.qt_comprou), 0), 0) AS cac
FROM meta m LEFT JOIN leads l USING (id_advertising)
WHERE m.lancamento IS NOT NULL
GROUP BY 1 HAVING leads > 500 ORDER BY invest DESC
