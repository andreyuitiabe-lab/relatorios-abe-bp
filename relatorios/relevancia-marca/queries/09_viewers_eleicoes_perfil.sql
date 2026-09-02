-- Viewers da playlist "BP nas Eleições" (sabatinas) — volume, perfil de plano e datas
-- Base do teste individual da hipótese "relevância baixa resistência na adesão"
SELECT
  nm_media,
  DATE(dt_created_at) AS dia,
  COUNT(DISTINCT nm_email) AS viewers,
  COUNT(DISTINCT IF(nm_plan IN ('free', 'fake-free'), nm_email, NULL)) AS viewers_freemium,
  COUNT(DISTINCT IF(nm_plan NOT IN ('free', 'fake-free'), nm_email, NULL)) AS viewers_membro,
  ROUND(SUM(vl_watch_time_seconds) / 3600, 1) AS horas
FROM datamart.obt_kafka__view_sessions
WHERE nm_playlist = 'BP nas Eleições'
  AND vl_watch_time_seconds >= 300
  AND nm_email IS NOT NULL
  AND DATE(dt_created_at) BETWEEN '2026-06-01' AND '2026-08-21'
GROUP BY 1, 2
ORDER BY 2, 1
