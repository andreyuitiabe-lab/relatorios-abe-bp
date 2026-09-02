-- Base do estudo de mCAC: spend e vendas diárias POR CAMPANHA Meta.
-- Cada salto de budget (|Δspend| ≥ 25%) vira um evento; o contrafactual são as
-- campanhas estáveis do mesmo dia. Método validado em midia-paga/VALIDACOES.md.
-- ⚠️ Spend Meta só existe desde 2025-08-01.
SELECT
  DATE(reference_date) AS dia,
  nm_campaign_name AS campanha,
  REGEXP_EXTRACT(nm_campaign_name, r'\[([A-Z0-9]+)\]') AS bloco1,
  REGEXP_EXTRACT(nm_campaign_name, r'\[[A-Z0-9]+\]\s*\[([A-Z0-9]+)\]') AS sigla,
  CASE
    WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[VENDA\]') THEN 'VENDA'
    WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]')  THEN 'LEAD'
    ELSE 'OUTRO'
  END AS fase,
  SUM(vl_amount_spent)  AS spend,
  SUM(qt_total_sales)   AS vendas,
  SUM(vl_total_revenue) AS receita,
  SUM(qt_impressions)   AS impressoes
FROM datamart.dtm_analytics_facebook_ads_funnel
WHERE DATE(reference_date) BETWEEN '2025-08-01' AND '2026-08-20'
GROUP BY 1, 2, 3, 4, 5
HAVING spend > 0
ORDER BY 1, 2
