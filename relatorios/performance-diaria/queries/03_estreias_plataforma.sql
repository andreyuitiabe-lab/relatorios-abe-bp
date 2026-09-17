-- Performance diária — estreias de conteúdo na plataforma: mídias cujo 1º dia com sessão ≥300s cai no dia,
-- com audiência D0 (usuários distintos). Filtro ≥100 usuários no D0 para separar estreia de QA/upload interno.
WITH s AS (
  SELECT nm_media, nm_playlist, DATE(dt_created_at) AS dia, LOWER(nm_email) AS email
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300 AND nm_email IS NOT NULL AND nm_media IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-01-01' AND '2026-09-13'
),
primeiro AS (
  SELECT nm_media, MIN(dia) AS estreia FROM s GROUP BY 1
),
d0 AS (
  SELECT s.nm_media, ANY_VALUE(s.nm_playlist) AS nm_playlist, p.estreia,
         COUNT(DISTINCT s.email) AS usuarios_d0
  FROM s JOIN primeiro p ON p.nm_media = s.nm_media AND s.dia = p.estreia
  GROUP BY 1, 3
)
SELECT estreia AS dia, nm_media, nm_playlist, usuarios_d0
FROM d0
WHERE estreia BETWEEN '2026-05-01' AND '2026-09-13' AND usuarios_d0 >= 100
ORDER BY 1, 4 DESC
