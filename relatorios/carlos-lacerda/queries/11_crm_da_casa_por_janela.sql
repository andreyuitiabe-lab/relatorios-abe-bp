-- Contexto obrigatorio para ler o volume de CRM de uma campanha: quanto a CASA
-- disparou no mesmo periodo. Campanha sem broadcast pode ser estrategia — ou regua
-- de CRM ocupada por outro lancamento.
SELECT
  CASE WHEN dt_dispatch_date <= '2026-07-31' THEN 'jul (D1-D3 ENE)' ELSE 'set (D1-D3 LAC)' END AS janela,
  nm_campaign_tag AS sigla,
  SUM(qt_insider_delivered) AS qt_entregues
FROM `bp-datawarehouse.datamart.dtm_analytics_revenue_insider_funnel`
WHERE nm_channel = 'email'
  AND (dt_dispatch_date BETWEEN '2026-07-28' AND '2026-07-30'
    OR dt_dispatch_date BETWEEN '2026-09-19' AND '2026-09-21')
GROUP BY 1, 2
HAVING qt_entregues > 100000
ORDER BY 1, 3 DESC
