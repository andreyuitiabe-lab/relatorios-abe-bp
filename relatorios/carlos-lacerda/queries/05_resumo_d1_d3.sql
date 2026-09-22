-- Anuncios DISTINTOS por sigla/fase nos 3 primeiros dias (o agregado do 01 cobre D1-D4;
-- somar o pico diario contaria o mesmo anuncio duas vezes).
SELECT
  IF(REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]'), 'LAC', 'ENE') AS sigla,
  IF(REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]'), 'LEAD', 'VENDA') AS fase,
  COUNT(DISTINCT IF(qt_impressions > 0, id_advertising, NULL)) AS qt_ads_distintos
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') AND reference_date BETWEEN '2026-09-19' AND '2026-09-21')
   OR (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[ene\]') AND reference_date BETWEEN '2026-07-28' AND '2026-07-30')
GROUP BY 1, 2
ORDER BY 1, 2
