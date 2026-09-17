-- RODADA 9 — "escalamos mantendo eficiência?" — semana 07–13/09 vs 31/08–06/09, por campanha e fonte.
-- Meta: dtm_analytics_facebook_ads_funnel · Google: dtm_analytics_google_ads_funnel (tipo pela nomenclatura).
WITH m AS (
  SELECT 'meta' AS fonte, DATE(reference_date) AS dia,
         COALESCE(REGEXP_EXTRACT(nm_campaign_name, r'\[[A-Z0-9]+\]\s*\[([A-Z0-9-]+)\]'), 'sem_sigla') AS sigla,
         CASE WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[VENDA\]') THEN 'VENDA'
              WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]') THEN 'LEAD' ELSE 'OUTRO' END AS fase,
         vl_amount_spent AS spend, qt_total_sales AS vendas, vl_total_revenue AS receita
  FROM datamart.dtm_analytics_facebook_ads_funnel
  UNION ALL
  SELECT 'google', DATE(reference_date),
         CASE WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[YT\]') THEN 'G_youtube'
              WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[KW\]') THEN 'G_busca_marca'
              WHEN REGEXP_CONTAINS(UPPER(nm_campaign_name), r'DISPLAY|DEMAND') THEN 'G_display'
              ELSE 'G_outros' END,
         CASE WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[VENDA\]') THEN 'VENDA'
              WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]') THEN 'LEAD' ELSE 'OUTRO' END,
         vl_amount_spent, qt_total_sales, vl_total_revenue
  FROM datamart.dtm_analytics_google_ads_funnel
  UNION ALL
  SELECT 'pmax', DATE(reference_date), 'G_pmax', 'VENDA', vl_amount_spent, qt_total_sales, vl_total_revenue
  FROM datamart.dtm_analytics_pmax_ads_funnel
)
SELECT fonte, sigla, fase,
  CASE WHEN dia BETWEEN '2026-08-31' AND '2026-09-06' THEN 'S1_31ago-06set' ELSE 'S2_07-13set' END AS semana,
  ROUND(SUM(spend)) AS spend, SUM(vendas) AS vendas, ROUND(SUM(receita)) AS receita,
  ROUND(SAFE_DIVIDE(SUM(spend), SUM(vendas))) AS cpa,
  ROUND(SAFE_DIVIDE(SUM(receita), SUM(spend)), 2) AS roas
FROM m
WHERE dia BETWEEN '2026-08-31' AND '2026-09-13'
GROUP BY 1, 2, 3, 4
HAVING spend > 2000
ORDER BY fonte, sigla, fase, semana
