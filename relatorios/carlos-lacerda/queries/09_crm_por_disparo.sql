-- Serie de e-mail POR DATA DE DISPARO (a stg conta por data do EVENTO e a cauda de
-- abertura do dia anterior contamina a serie). Usada para ler fadiga de lista.
SELECT
  nm_campaign_tag AS sigla,
  dt_dispatch_date AS dt,
  nm_channel AS canal,
  COUNT(DISTINCT nm_campaign) AS qt_pecas,
  SUM(qt_insider_delivered) AS qt_entregues,
  SUM(qt_insider_read_or_open) AS qt_aberturas,
  SUM(qt_insider_click) AS qt_cliques,
  SUM(qt_insider_unsubscribe) AS qt_descadastros,
  SUM(qt_insider_spamreport) AS qt_spam,
  ROUND(SUM(vl_total_revenue)) AS vl_receita
FROM `bp-datawarehouse.datamart.dtm_analytics_revenue_insider_funnel`
WHERE (nm_campaign_tag = 'LAC' AND dt_dispatch_date BETWEEN '2026-09-19' AND '2026-09-21')
   OR (nm_campaign_tag = 'ENE' AND dt_dispatch_date BETWEEN '2026-07-28' AND '2026-07-30')
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
