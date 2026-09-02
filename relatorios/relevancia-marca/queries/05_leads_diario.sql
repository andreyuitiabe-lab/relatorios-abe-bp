-- Leads diários: total, mídia paga e orgânicos (proxy SECUNDÁRIO de atenção —
-- leads correlacionam com campanha/LP ativa, não com relevância; nota do André no plano)
SELECT
  DATE(dt_registered_at_br) AS dia,
  COUNT(DISTINCT nm_email) AS leads_total,
  COUNT(DISTINCT IF(
    LOWER(COALESCE(utm_source, '')) LIKE '%face%'
    OR LOWER(COALESCE(utm_source, '')) IN ('ig', 'fb', 'pmax', 'google', 'google_ads', 'adwords', 'twitter', 'tiktok'),
    nm_email, NULL)) AS leads_pagos,
  COUNT(DISTINCT IF(
    LOWER(COALESCE(utm_source, '')) NOT LIKE '%face%'
    AND LOWER(COALESCE(utm_source, '')) NOT IN ('ig', 'fb', 'pmax', 'google', 'google_ads', 'adwords', 'twitter', 'tiktok'),
    nm_email, NULL)) AS leads_organicos
FROM datamart.dtm_analytics_lead_conversion
WHERE DATE(dt_registered_at_br) BETWEEN '2025-08-01' AND '2026-08-20'
GROUP BY 1
ORDER BY 1
