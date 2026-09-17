-- Performance diária — spend, vendas e receita atribuídas pela plataforma, por dia × fonte × sigla × fase.
-- Meta e Google pela nomenclatura de campanha; PMax sem sigla (campanha por produto).
WITH m AS (
  SELECT 'meta' AS fonte, DATE(reference_date) AS dia,
         COALESCE(REGEXP_EXTRACT(nm_campaign_name, r'\[[A-Z0-9]+\]\s*\[([A-Z0-9-]+)\]'), 'sem_sigla') AS sigla,
         CASE WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[VENDA\]') THEN 'VENDA'
              WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]') THEN 'LEAD' ELSE 'OUTRO' END AS fase,
         vl_amount_spent AS spend, qt_total_sales AS vendas, vl_total_revenue AS receita
  FROM datamart.dtm_analytics_facebook_ads_funnel
  UNION ALL
  SELECT 'google', DATE(reference_date),
         COALESCE(REGEXP_EXTRACT(nm_campaign_name, r'\[[A-Z0-9]+\]\s*\[([A-Z0-9-]+)\]'), 'sem_sigla'),
         CASE WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[VENDA\]') THEN 'VENDA'
              WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]') THEN 'LEAD' ELSE 'OUTRO' END,
         vl_amount_spent, qt_total_sales, vl_total_revenue
  FROM datamart.dtm_analytics_google_ads_funnel
  UNION ALL
  SELECT 'pmax', DATE(reference_date), 'PMAX', 'VENDA', vl_amount_spent, qt_total_sales, vl_total_revenue
  FROM datamart.dtm_analytics_pmax_ads_funnel
)
SELECT fonte, dia, sigla, fase,
  ROUND(SUM(spend), 2) AS spend, SUM(vendas) AS vendas, ROUND(SUM(receita), 2) AS receita
FROM m
WHERE dia BETWEEN '2026-05-01' AND '2026-09-13'
GROUP BY 1, 2, 3, 4
HAVING spend > 0 OR vendas > 0
ORDER BY 2, 1, 3
