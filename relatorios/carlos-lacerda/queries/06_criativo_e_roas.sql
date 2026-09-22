-- Engajamento de criativo e retorno de midia, D1-D3, so campanhas [VENDA].
-- ⚠️ Anuncio ESTATICO nao gera qt_three_second_views (vem NULL) — incluir esses no
-- denominador derruba o hook rate agregado sem que nenhum video tenha piorado.
-- Hook e hold sao calculados SO sobre anuncios com metrica de video.
WITH por_ad AS (
  SELECT
    IF(REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]'), 'LAC', 'ENE') AS sigla,
    id_advertising,
    SUM(qt_impressions) AS i, SUM(qt_three_second_views) AS v3, SUM(qt_thruplays) AS tp,
    SUM(vl_amount_spent) AS s, SUM(qt_outbound_clicks) AS c,
    SUM(vl_total_revenue) AS rec, SUM(qt_total_sales) AS vd
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE ((REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') AND reference_date BETWEEN '2026-09-19' AND '2026-09-21')
      OR (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[ene\]') AND reference_date BETWEEN '2026-07-28' AND '2026-07-30'))
    AND NOT REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]')
  GROUP BY 1, 2
  HAVING i > 0
)
SELECT
  sigla,
  COUNT(*) AS qt_ads,
  COUNTIF(v3 IS NULL OR v3 = 0) AS qt_ads_sem_video,
  ROUND(SUM(IF(v3 > 0, 0, i)) / SUM(i) * 100, 1) AS pct_impr_sem_video,
  ROUND(SUM(IF(v3 > 0, v3, 0)) / NULLIF(SUM(IF(v3 > 0, i, 0)), 0) * 100, 1) AS hook_rate_video_pct,
  ROUND(SUM(IF(v3 > 0, tp, 0)) / NULLIF(SUM(IF(v3 > 0, v3, 0)), 0) * 100, 1) AS hold_rate_video_pct,
  ROUND(SUM(c) / SUM(i) * 100, 2) AS ctr_pct,
  ROUND(SUM(s) / SUM(c), 2) AS cpc,
  SUM(vd) AS qt_vendas_meta,
  ROUND(SUM(rec)) AS vl_receita_meta,
  ROUND(SUM(rec) / SUM(s), 2) AS roas_midia,
  ROUND(SUM(s) / NULLIF(SUM(vd), 0)) AS custo_por_venda
FROM por_ad
GROUP BY 1
ORDER BY 1
