-- TESTE B (médio prazo) — Q24: censura à direita por sabatina.
-- Última data COMPLETA em fct_transactions: 2026-09-01 (medido 02/09/2026; 02/09 parcial,
-- 03/09+ são registros futuros espúrios). Um pessoa-dia em dia d tem a janela D+k completa
-- se d + k <= 2026-09-01, i.e. d <= cutoff(k):
--   D+14 -> 2026-08-18 | D+30 -> 2026-08-02 | D+60 -> 2026-07-03 | D+90 -> 2026-06-03
-- A playlist estreou em 2026-06-08 => D+90 tem ZERO pessoa-dias elegíveis (infactível hoje).
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_media
  FROM datamart.obt_kafka__view_sessions
  WHERE nm_playlist = 'BP nas Eleições'
    AND vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
),

pd AS (
  SELECT nm_media, email, dia
  FROM sessoes
  GROUP BY 1, 2, 3
)

SELECT
  nm_media AS sabatina,
  MIN(dia) AS primeiro_dia,
  MAX(dia) AS ultimo_dia,
  COUNT(*) AS pessoa_dias_total,
  COUNTIF(dia <= '2026-08-18') AS pd_d14,
  COUNTIF(dia <= '2026-08-02') AS pd_d30,
  COUNTIF(dia <= '2026-07-03') AS pd_d60,
  COUNTIF(dia <= '2026-06-03') AS pd_d90
FROM pd
GROUP BY 1
ORDER BY 2
