-- TESTE INDIVIDUAL v3 — corrige 2 vieses do v2:
--   (a) causalidade reversa: outcome passa a ser D+1..D+14 (exclui compra no mesmo dia)
--   (b) controle injusto: em vez de "todo outro conteúdo", compara a sabatina contra
--       as playlists de conteúdo corrente mais assistidas (placebo de "conteúdo novo/em alta")
-- Estratos: só pessoas JÁ ativas nos 30d anteriores (exclui o estrato contaminado "novo")
WITH sessoes AS (
  SELECT
    LOWER(nm_email) AS email,
    DATE(dt_created_at) AS dia,
    nm_playlist,
    nm_plan,
    vl_watch_time_seconds AS seg
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-03-01' AND '2026-08-07'
),

top_playlists AS (  -- playlists de referência (maior audiência no período)
  SELECT nm_playlist
  FROM sessoes
  WHERE nm_playlist IS NOT NULL AND nm_playlist != 'BP nas Eleições'
  GROUP BY 1
  ORDER BY COUNT(DISTINCT email) DESC
  LIMIT 8
),

pessoa_dia AS (
  SELECT
    s.email,
    s.dia,
    MAX(IF(s.nm_playlist = 'BP nas Eleições', 1, 0)) AS viu_sabatina,
    MAX(IF(s.nm_playlist IN (SELECT nm_playlist FROM top_playlists), 1, 0)) AS viu_top,
    MAX(IF(s.nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium
  FROM sessoes s
  GROUP BY 1, 2
),

engaj AS (
  SELECT pd.email, pd.dia, COUNT(DISTINCT s.dia) AS dias_ativos_30d
  FROM pessoa_dia pd
  LEFT JOIN sessoes s
    ON s.email = pd.email
   AND s.dia BETWEEN DATE_SUB(pd.dia, INTERVAL 30 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)
  GROUP BY 1, 2
),

compras AS (
  SELECT LOWER(c.nm_email) AS email, DATE(t.dt_ordered_at) AS dia_compra, t.vl_payment_gross AS vl
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) BETWEEN '2026-03-01' AND '2026-08-21'
),

base AS (
  SELECT
    pd.email, pd.dia, pd.eh_freemium,
    CASE WHEN pd.viu_sabatina = 1 THEN 'sabatina'
         WHEN pd.viu_top = 1 THEN 'top_playlist'
         ELSE 'outro' END AS grupo,
    CASE WHEN e.dias_ativos_30d <= 2 THEN '1_leve'
         WHEN e.dias_ativos_30d <= 8 THEN '2_medio'
         ELSE '3_heavy' END AS faixa_engaj,
    (SELECT COUNT(*) FROM compras c
      WHERE c.email = pd.email
        AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS n_compras,
    (SELECT SUM(c.vl) FROM compras c
      WHERE c.email = pd.email
        AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS receita
  FROM pessoa_dia pd
  JOIN engaj e USING (email, dia)
  WHERE e.dias_ativos_30d >= 1  -- só já-ativos: remove o estrato com causalidade reversa
)

SELECT
  IF(eh_freemium = 1, 'freemium', 'membro') AS status,
  faixa_engaj,
  grupo,
  COUNT(*) AS pessoa_dias,
  COUNTIF(n_compras > 0) AS com_compra_d1_d14,
  ROUND(100 * COUNTIF(n_compras > 0) / COUNT(*), 3) AS tx_compra_pct,
  ROUND(SUM(COALESCE(receita, 0)) / COUNT(*), 2) AS receita_por_pessoa_dia
FROM base
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
