-- Ads da campanha Odisseia: Meta (dia) + Meta/Google/PMax (campanha).
-- Filtro: nm_campaign_name com '[ODI]' ou 'ODISSEIA'. Spend começa 03/07/2026.
-- Janela dinâmica no refresh.py. Snapshot: 01/07–12/08/2026.

-- 1) Meta por dia
SELECT reference_date AS dia, ROUND(SUM(vl_amount_spent),0) AS spend,
       SUM(qt_impressions) AS impr, SUM(qt_outbound_clicks) AS clicks,
       SUM(qt_total_sales) AS vendas, ROUND(SUM(vl_total_revenue),0) AS receita,
       SUM(qt_commercial_total_sales) AS vendas_com
FROM datamart.dtm_analytics_facebook_ads_funnel
WHERE (UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%')
  AND reference_date >= '2026-07-01'
GROUP BY 1 ORDER BY 1;

-- 2) Por campanha (Meta + Google + PMax), com ROAS
SELECT fonte, campanha, spend, impr, clicks, vendas_dir, vendas_com, vendas, receita,
       ROUND(receita/NULLIF(spend,0), 2) AS roas
FROM (
  SELECT 'Meta' AS fonte, nm_campaign_name AS campanha, ROUND(SUM(vl_amount_spent),0) AS spend,
         SUM(qt_impressions) AS impr, SUM(qt_outbound_clicks) AS clicks,
         SUM(qt_direct_sales) AS vendas_dir, SUM(qt_commercial_total_sales) AS vendas_com,
         SUM(qt_total_sales) AS vendas, ROUND(SUM(vl_total_revenue),0) AS receita
  FROM datamart.dtm_analytics_facebook_ads_funnel
  WHERE (UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%')
    AND reference_date >= '2026-07-01'
  GROUP BY 2
  UNION ALL
  SELECT 'Google', nm_campaign_name, ROUND(SUM(vl_amount_spent),0), SUM(qt_impressions), SUM(qt_outbound_clicks),
         SUM(qt_direct_sales), SUM(qt_commercial_total_sales), SUM(qt_total_sales), ROUND(SUM(vl_total_revenue),0)
  FROM datamart.dtm_analytics_google_ads_funnel
  WHERE (UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%')
    AND reference_date >= '2026-07-01'
  GROUP BY 2
  UNION ALL
  SELECT 'PMax', nm_campaign_name, ROUND(SUM(vl_amount_spent),0), SUM(qt_impressions), SUM(qt_outbound_clicks),
         SUM(qt_direct_sales), SUM(qt_commercial_total_sales), SUM(qt_total_sales), ROUND(SUM(vl_total_revenue),0)
  FROM datamart.dtm_analytics_pmax_ads_funnel
  WHERE (UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%')
    AND reference_date >= '2026-07-01'
  GROUP BY 2
)
ORDER BY spend DESC;
