-- CRM Insider: disparos nos 4 primeiros dias — LAC x ENE
SELECT
  nm_campaign_tag AS sigla,
  nm_channel,
  DATE_DIFF(dt_dispatch_date, IF(nm_campaign_tag = 'LAC', DATE '2026-09-19', DATE '2026-07-28'), DAY) + 1 AS dia,
  dt_dispatch_date,
  COUNT(DISTINCT nm_campaign) AS qt_pecas,
  SUM(qt_insider_delivered) AS qt_entregues,
  SUM(qt_insider_read_or_open) AS qt_aberturas,
  SUM(qt_insider_click) AS qt_cliques,
  ROUND(SUM(qt_insider_read_or_open) / NULLIF(SUM(qt_insider_delivered), 0) * 100, 2) AS tx_abertura_pct,
  ROUND(SUM(qt_insider_click) / NULLIF(SUM(qt_insider_delivered), 0) * 100, 2) AS tx_clique_pct,
  ROUND(SUM(vl_total_revenue)) AS vl_receita
FROM `bp-datawarehouse.datamart.dtm_analytics_revenue_insider_funnel`
WHERE (nm_campaign_tag = 'LAC' AND dt_dispatch_date BETWEEN '2026-09-19' AND '2026-09-22')
   OR (nm_campaign_tag = 'ENE' AND dt_dispatch_date BETWEEN '2026-07-28' AND '2026-07-31')
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3
