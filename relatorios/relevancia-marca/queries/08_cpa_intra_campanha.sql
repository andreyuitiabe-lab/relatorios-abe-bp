-- Teste da hipótese "relevância baixa resistência", controlando MIX de campanha:
-- dentro da mesma campanha [VENDA], o CPA e o ROAS melhoraram nas janelas das sabatinas?
-- Comparação: 14–19/08 (janelas) vs 17/07–13/08 (pré, mesma campanha)
WITH diario AS (
  SELECT
    REGEXP_EXTRACT(nm_campaign_name, r'\[[A-Z0-9]+\]\s*\[([A-Z0-9]+)\]') AS sigla,
    DATE(reference_date) AS dia,
    SUM(vl_amount_spent) AS spend,
    SUM(qt_total_sales) AS vendas,
    SUM(vl_total_revenue) AS receita
  FROM datamart.dtm_analytics_facebook_ads_funnel
  WHERE DATE(reference_date) BETWEEN '2026-07-17' AND '2026-08-19'
    AND REGEXP_CONTAINS(nm_campaign_name, r'\[VENDA\]')
  GROUP BY 1, 2
)
SELECT
  sigla,
  ROUND(SUM(IF(dia >= '2026-08-14', spend, 0))) AS spend_jan,
  ROUND(SAFE_DIVIDE(SUM(IF(dia >= '2026-08-14', spend, 0)), SUM(IF(dia >= '2026-08-14', vendas, 0))), 2) AS cpa_jan,
  ROUND(SAFE_DIVIDE(SUM(IF(dia < '2026-08-14', spend, 0)), SUM(IF(dia < '2026-08-14', vendas, 0))), 2) AS cpa_pre,
  ROUND(SAFE_DIVIDE(SUM(IF(dia >= '2026-08-14', receita, 0)), SUM(IF(dia >= '2026-08-14', spend, 0))), 2) AS roas_jan,
  ROUND(SAFE_DIVIDE(SUM(IF(dia < '2026-08-14', receita, 0)), SUM(IF(dia < '2026-08-14', spend, 0))), 2) AS roas_pre,
  ROUND(100 * SAFE_DIVIDE(SUM(IF(dia >= '2026-08-14', spend, 0)) / 6, SUM(IF(dia < '2026-08-14', spend, 0)) / 28) - 100) AS pct_escala_spend
FROM diario
GROUP BY 1
HAVING spend_jan > 10000
ORDER BY spend_jan DESC
