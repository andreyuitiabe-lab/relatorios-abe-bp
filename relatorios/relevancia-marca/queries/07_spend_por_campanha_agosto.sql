-- O que puxou o spend nas janelas das sabatinas (14–19/08) vs baseline pré (17/07–13/08)
-- Objetivo: separar "relevância" de "escala de mídia" — o spend subiu 55–81% nas janelas
SELECT
  REGEXP_EXTRACT(nm_campaign_name, r'\[[A-Z0-9]+\]\s*\[([A-Z0-9]+)\]') AS sigla,
  REGEXP_CONTAINS(nm_campaign_name, r'\[VENDA\]') AS eh_venda,
  ROUND(SUM(IF(DATE(reference_date) BETWEEN '2026-08-14' AND '2026-08-19', vl_amount_spent, 0))) AS spend_janelas_6d,
  ROUND(SUM(IF(DATE(reference_date) BETWEEN '2026-07-17' AND '2026-08-13', vl_amount_spent, 0)) / 28 * 6) AS spend_pre_equiv_6d,
  SUM(IF(DATE(reference_date) BETWEEN '2026-08-14' AND '2026-08-19', qt_total_sales, 0)) AS vendas_janelas,
  ROUND(SUM(IF(DATE(reference_date) BETWEEN '2026-08-14' AND '2026-08-19', vl_total_revenue, 0))) AS receita_janelas
FROM datamart.dtm_analytics_facebook_ads_funnel
WHERE DATE(reference_date) BETWEEN '2026-07-17' AND '2026-08-19'
GROUP BY 1, 2
HAVING spend_janelas_6d > 5000
ORDER BY spend_janelas_6d DESC
