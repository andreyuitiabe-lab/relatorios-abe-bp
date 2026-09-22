-- Meta Ads: 4 primeiros dias de veiculacao — LAC (19-22/09/2026) x ENE (28-31/07/2026)
-- D1 = primeiro dia com spend registrado
WITH base AS (
  SELECT
    CASE WHEN REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') THEN 'LAC' ELSE 'ENE' END AS sigla,
    CASE WHEN REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]') THEN 'LEAD' ELSE 'VENDA' END AS fase,
    DATE_DIFF(reference_date,
      CASE WHEN REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') THEN DATE '2026-09-19' ELSE DATE '2026-07-28' END,
      DAY) + 1 AS dia,
    reference_date, id_advertising, vl_amount_spent, qt_impressions, qt_outbound_clicks,
    qt_three_second_views, qt_thruplays, qt_total_sales, vl_total_revenue
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') AND reference_date BETWEEN '2026-09-19' AND '2026-09-22')
     OR (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[ene\]') AND reference_date BETWEEN '2026-07-28' AND '2026-07-31')
)
SELECT
  sigla, fase, dia, MIN(reference_date) AS dt,
  COUNT(DISTINCT IF(qt_impressions > 0, id_advertising, NULL)) AS qt_ads_ativos,
  ROUND(SUM(vl_amount_spent)) AS vl_spend,
  SUM(qt_impressions) AS qt_impressoes,
  ROUND(SUM(vl_amount_spent) / NULLIF(SUM(qt_impressions), 0) * 1000, 2) AS cpm,
  SUM(qt_outbound_clicks) AS qt_cliques,
  ROUND(SUM(qt_outbound_clicks) / NULLIF(SUM(qt_impressions), 0) * 100, 2) AS ctr_pct,
  ROUND(SUM(vl_amount_spent) / NULLIF(SUM(qt_outbound_clicks), 0), 2) AS cpc,
  ROUND(SUM(qt_three_second_views) / NULLIF(SUM(qt_impressions), 0) * 100, 1) AS hook_rate_pct,
  ROUND(SUM(qt_thruplays) / NULLIF(SUM(qt_three_second_views), 0) * 100, 1) AS hold_rate_pct,
  SUM(qt_total_sales) AS qt_vendas,
  ROUND(SUM(vl_total_revenue)) AS vl_receita
FROM base
GROUP BY ROLLUP(sigla, fase, dia)
HAVING sigla IS NOT NULL
ORDER BY sigla, fase NULLS LAST, dia NULLS LAST
