-- Views da LP Black November e do checkout R$ 1,90 em blocos de 5 min (horário de Brasília), 04/10 12h → 05/10 03h.
-- "live" = chegou com o link da live (utm_content=apuracao_eleicoes_04out).
WITH e AS (
  SELECT TIMESTAMP_TRUNC(TIMESTAMP_MICROS(event_timestamp), MINUTE) ts,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') loc
  FROM `bp-lake.analytics_378996649.events_*`
  WHERE _TABLE_SUFFIX IN ('20261004', '20261005') AND event_name = 'page_view'
)
SELECT
  FORMAT_DATETIME('%Y-%m-%d %H:%M', DATETIME(TIMESTAMP_SECONDS(DIV(UNIX_SECONDS(ts), 300) * 300), 'America/Sao_Paulo')) AS bloco,
  COUNTIF(loc LIKE '%black-november-2026%' AND loc LIKE '%apuracao_eleicoes%') AS lp_live,
  COUNTIF(loc LIKE '%black-november-2026%') AS lp_total,
  COUNTIF(loc LIKE '%go.brasilparalelo.com.br/subscribe/mkt-anual-assine-por-r-1-90%') AS checkout
FROM e
WHERE DATETIME(ts, 'America/Sao_Paulo') BETWEEN '2026-10-04 12:00:00' AND '2026-10-05 02:59:59'
GROUP BY 1
ORDER BY 1
