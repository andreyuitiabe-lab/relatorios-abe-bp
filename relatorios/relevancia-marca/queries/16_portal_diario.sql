-- Série diária do portal (Mixpanel): page views e leadwall por origem
-- Orgânico = sem utm de mídia paga. Proxy de atenção espontânea ao conteúdo do portal.
WITH pv AS (
  SELECT
    DATE(event_timestamp) AS dia,
    session_id,
    device_id,
    LOWER(COALESCE(utm_source, '')) AS src,
    LOWER(COALESCE(utm_medium, '')) AS med,
    LOWER(COALESCE(page_referrer, '')) AS ref
  FROM events.fct_mixpanel__portal_page_view_events
  WHERE DATE(event_timestamp) BETWEEN '2025-08-01' AND '2026-08-20'
),

classificado AS (
  SELECT
    dia, session_id, device_id,
    CASE
      WHEN REGEXP_CONTAINS(src, r'face|^ig$|^fb$|instagram|pmax|google_ads|adwords|taboola|twitter|tiktok')
           OR REGEXP_CONTAINS(med, r'cpc|paid|ads|pmax') THEN 'pago'
      WHEN REGEXP_CONTAINS(ref, r'youtube|youtu\.be') THEN 'youtube_org'
      WHEN REGEXP_CONTAINS(ref, r'instagram|facebook|twitter|x\.com|t\.co|tiktok|whatsapp') THEN 'social_org'
      WHEN REGEXP_CONTAINS(ref, r'google|bing|duckduckgo|search\.') THEN 'busca_org'
      WHEN ref = '' AND src = '' THEN 'direto'
      ELSE 'outro'
    END AS origem
  FROM pv
)

SELECT
  dia,
  COUNT(*) AS pageviews_total,
  COUNT(DISTINCT device_id) AS devices_total,
  COUNT(DISTINCT IF(origem != 'pago', device_id, NULL)) AS devices_organicos,
  COUNT(DISTINCT IF(origem = 'youtube_org', device_id, NULL)) AS devices_youtube_org,
  COUNT(DISTINCT IF(origem = 'social_org', device_id, NULL)) AS devices_social_org,
  COUNT(DISTINCT IF(origem = 'busca_org', device_id, NULL)) AS devices_busca_org,
  COUNT(DISTINCT IF(origem = 'direto', device_id, NULL)) AS devices_direto,
  COUNT(DISTINCT IF(origem = 'pago', device_id, NULL)) AS devices_pago
FROM classificado
GROUP BY 1
ORDER BY 1
