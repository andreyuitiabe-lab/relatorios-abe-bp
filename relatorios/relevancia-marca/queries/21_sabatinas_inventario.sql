-- TESTE A (formato vs pauta) — Inventário das 9 sabatinas da playlist `BP nas Eleições`.
-- Estreia NA PLATAFORMA (min data de sessão ≥300s) e pessoa-dias de audiência.
-- ⚠️ Achado: Renan e Marçal só entraram na plataforma em 19/08/2026 (as lives de 14/08 e
-- 17/08 foram no YouTube) → a query 14 original (sessões até 07/08) mediu o IAC 1,98×
-- da playlist SEM nenhum pessoa-dia de Renan/Marçal.
SELECT
  nm_media,
  MIN(DATE(dt_created_at)) AS estreia_plataforma,
  COUNT(DISTINCT CONCAT(LOWER(nm_email), '|', CAST(DATE(dt_created_at) AS STRING))) AS pessoa_dias,
  COUNT(DISTINCT LOWER(nm_email)) AS pessoas,
  COUNT(DISTINCT IF(nm_plan NOT IN ('free', 'fake-free'),
    CONCAT(LOWER(nm_email), '|', CAST(DATE(dt_created_at) AS STRING)), NULL)) AS pessoa_dias_membro
FROM datamart.obt_kafka__view_sessions
WHERE nm_playlist = 'BP nas Eleições'
  AND vl_watch_time_seconds >= 300
  AND nm_email IS NOT NULL
GROUP BY 1
ORDER BY estreia_plataforma
