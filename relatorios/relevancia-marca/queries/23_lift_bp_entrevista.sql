-- TESTE A (formato vs pauta) — mesma máquina da query 22 para episódios INDIVIDUAIS de
-- `BP Entrevista` (régua de formato: entrevista SEM pauta eleitoral). Top-5 episódios por
-- pessoa-dias na janela. Janela de pessoa-dias: 01/03/2026 (alinha com a query 14/15) a
-- 18/08/2026 (D+14 completo com compras até 01/09). Comparador: top-8 playlists
-- (excl. BP nas Eleições e BP Entrevista), saída por (grupo, dia) p/ pareamento por calendário.
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_playlist, nm_media, nm_plan
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-01-30' AND '2026-08-18'  -- 30/01 p/ lookback de engajamento
),

janela AS (
  SELECT * FROM sessoes WHERE dia BETWEEN '2026-03-01' AND '2026-08-18'
),

top_playlists AS (
  SELECT nm_playlist FROM janela
  WHERE nm_playlist IS NOT NULL
    AND nm_playlist NOT IN ('BP nas Eleições', 'BP Entrevista')
  GROUP BY 1 ORDER BY COUNT(DISTINCT email) DESC LIMIT 8
),

top_episodios AS (
  SELECT nm_media FROM janela
  WHERE nm_playlist = 'BP Entrevista'
  GROUP BY 1
  ORDER BY COUNT(DISTINCT CONCAT(email, '|', CAST(dia AS STRING))) DESC
  LIMIT 5
),

pessoa_dia AS (
  SELECT email, dia,
    MAX(IF(nm_playlist = 'BP Entrevista', 1, 0)) AS viu_entrevista,
    MAX(IF(nm_playlist = 'BP nas Eleições', 1, 0)) AS viu_sabatina,
    MAX(IF(nm_playlist IN (SELECT nm_playlist FROM top_playlists), 1, 0)) AS viu_top,
    MAX(IF(nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium
  FROM janela GROUP BY 1, 2
),

episodio_media AS (
  SELECT DISTINCT email, dia, nm_media
  FROM janela
  WHERE nm_playlist = 'BP Entrevista'
    AND nm_media IN (SELECT nm_media FROM top_episodios)
),

engaj AS (
  SELECT pd.email, pd.dia, COUNT(DISTINCT s.dia) AS dias_ativos_30d
  FROM pessoa_dia pd
  LEFT JOIN sessoes s ON s.email = pd.email
   AND s.dia BETWEEN DATE_SUB(pd.dia, INTERVAL 30 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)
  GROUP BY 1, 2
),

compras AS (
  SELECT LOWER(c.nm_email) AS email, DATE(t.dt_ordered_at) AS dia_compra, t.vl_payment_gross AS vl
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) BETWEEN '2026-01-01' AND '2026-09-01'
),

base AS (
  SELECT pd.email, pd.dia, pd.viu_entrevista, pd.viu_sabatina, pd.viu_top,
    (SELECT COUNT(*) FROM compras c WHERE c.email = pd.email
       AND c.dia_compra BETWEEN DATE_SUB(pd.dia, INTERVAL 60 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)) AS compra_60d,
    (SELECT COUNT(*) FROM compras c WHERE c.email = pd.email
       AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 7 DAY)) AS pos7,
    (SELECT COUNT(*) FROM compras c WHERE c.email = pd.email
       AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS pos14,
    (SELECT SUM(c.vl) FROM compras c WHERE c.email = pd.email
       AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 7 DAY)) AS receita7,
    (SELECT SUM(c.vl) FROM compras c WHERE c.email = pd.email
       AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS receita14
  FROM pessoa_dia pd
  JOIN engaj e USING (email, dia)
  WHERE pd.eh_freemium = 0
    AND e.dias_ativos_30d BETWEEN 1 AND 8
)

SELECT em.nm_media AS grupo, b.dia,
  COUNT(*) AS pessoa_dias,
  COUNTIF(b.pos7 > 0) AS com_compra_d7,
  COUNTIF(b.pos14 > 0) AS com_compra_d14,
  ROUND(SUM(COALESCE(b.receita7, 0)), 2) AS receita_d7,
  ROUND(SUM(COALESCE(b.receita14, 0)), 2) AS receita_d14
FROM base b
JOIN episodio_media em USING (email, dia)
WHERE b.compra_60d = 0
GROUP BY 1, 2

UNION ALL

SELECT 'CONTROLE_top8' AS grupo, dia,
  COUNT(*) AS pessoa_dias,
  COUNTIF(pos7 > 0) AS com_compra_d7,
  COUNTIF(pos14 > 0) AS com_compra_d14,
  ROUND(SUM(COALESCE(receita7, 0)), 2) AS receita_d7,
  ROUND(SUM(COALESCE(receita14, 0)), 2) AS receita_d14
FROM base
WHERE compra_60d = 0 AND viu_entrevista = 0 AND viu_sabatina = 0 AND viu_top = 1
GROUP BY 1, 2
ORDER BY 1, 2
