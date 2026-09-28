-- O que os membros assistem NA PLATAFORMA, e em que dispositivo.
-- Contraparte da audiência do YouTube: mesma pergunta, outro lugar.
-- Fonte: datamart.obt_kafka__view_sessions (ver bq-acesso.md e bq-regras.md).

-- ── 1. dispositivo de consumo (comparar com deviceType do YouTube) ──────────
SELECT
  COALESCE(nm_summary_client, '?')                                   AS cliente,
  COUNT(*)                                                           AS sessoes,
  ROUND(SUM(vl_watch_time_seconds) / 3600)                           AS horas,
  ROUND(100 * SUM(vl_watch_time_seconds)
            / SUM(SUM(vl_watch_time_seconds)) OVER (), 1)            AS pct_horas
FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
WHERE DATE(dt_created_at) BETWEEN '2026-01-01' AND '2026-09-19'
GROUP BY cliente
ORDER BY horas DESC;

-- ── 2. playlists mais assistidas (comparar com o top do YouTube) ────────────
SELECT
  nm_playlist,
  ROUND(SUM(vl_watch_time_seconds) / 3600)  AS horas,
  COUNT(DISTINCT id_user)                   AS users,
  ANY_VALUE(bl_is_original_bp)              AS original_bp
FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
WHERE DATE(dt_created_at) BETWEEN '2026-01-01' AND '2026-09-19'
  AND nm_playlist IS NOT NULL
GROUP BY nm_playlist
ORDER BY horas DESC
LIMIT 20;
