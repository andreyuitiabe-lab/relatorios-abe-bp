-- Usuários GA4 (cookie) que viram a LP e o checkout em 04/10. O GA4 conta menos que o real (consentimento, bloqueador).
SELECT
  COUNT(DISTINCT IF(loc LIKE '%black-november-2026%', u, NULL)) AS lp_usuarios,
  COUNT(DISTINCT IF(loc LIKE '%go.brasilparalelo.com.br/subscribe/%', u, NULL)) AS checkout_usuarios
FROM (
  SELECT user_pseudo_id AS u, (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS loc
  FROM `bp-lake.analytics_378996649.events_20261004`
  WHERE event_name = 'page_view'
)
