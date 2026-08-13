-- CRM da campanha Odisseia no Insider. Tag real nos dados: nm_campaign_tag = 'ODI'
-- (a nomenclatura oficial da wiki dizia ODD — corrigido em 13/08/2026).
-- Janela dinâmica no refresh.py. Snapshot: 01/07–12/08/2026.

-- 1) Por dia e canal
SELECT dt_dispatch_date AS dia, nm_channel AS canal,
       SUM(qt_insider_delivered) AS entregues,
       SUM(qt_insider_read_or_open) AS aberturas,   -- email: só abertura humana desde mar/2026
       SUM(qt_insider_click) AS clicks,
       SUM(qt_total_sales) AS vendas, ROUND(SUM(vl_total_revenue),0) AS receita
FROM datamart.dtm_analytics_revenue_insider_funnel
WHERE UPPER(nm_campaign_tag)='ODI' AND dt_dispatch_date >= '2026-07-01'
GROUP BY 1,2 ORDER BY 1;

-- 2) Top peças por receita (direto + comercial)
SELECT nm_channel AS canal, nm_campaign AS peca,
       SUM(qt_insider_delivered) AS entregues, SUM(qt_insider_click) AS clicks,
       SUM(qt_total_sales) AS vendas, ROUND(SUM(vl_total_revenue),0) AS receita,
       ROUND(SUM(vl_total_revenue)/NULLIF(SUM(qt_insider_delivered),0)*1000,0) AS receita_por_1k
FROM datamart.dtm_analytics_revenue_insider_funnel
WHERE UPPER(nm_campaign_tag)='ODI' AND dt_dispatch_date >= '2026-07-01'
GROUP BY 1,2 HAVING receita > 0 ORDER BY receita DESC LIMIT 20;
