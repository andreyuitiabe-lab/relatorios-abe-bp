-- RODADA 9a (auditoria) — erro-padrão CLUSTERIZADO POR PESSOA para o Teste B (query 25):
-- universo comum 08/06–03/07/2026, janelas D+1..14 / 30 / 60. Mesma máquina da query 25;
-- saída por grupo com soma de quadrados por pessoa (ver 27_cluster_robusto_q14.sql).
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_playlist, nm_plan
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-05-09' AND '2026-07-03'
),

top_playlists AS (
  SELECT nm_playlist FROM sessoes
  WHERE nm_playlist IS NOT NULL AND nm_playlist != 'BP nas Eleições'
    AND dia BETWEEN '2026-06-08' AND '2026-07-03'
  GROUP BY 1 ORDER BY COUNT(DISTINCT email) DESC LIMIT 8
),

pessoa_dia AS (
  SELECT s.email, s.dia,
    MAX(IF(s.nm_playlist = 'BP nas Eleições', 1, 0)) AS viu_sabatina,
    MAX(IF(s.nm_playlist IN (SELECT nm_playlist FROM top_playlists), 1, 0)) AS viu_top,
    MAX(IF(s.nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium
  FROM sessoes s
  WHERE s.dia BETWEEN '2026-06-08' AND '2026-07-03'
  GROUP BY 1, 2
),

engaj AS (
  SELECT pd.email, pd.dia, COUNT(DISTINCT s.dia) AS dias_ativos_30d
  FROM pessoa_dia pd
  LEFT JOIN sessoes s ON s.email = pd.email
   AND s.dia BETWEEN DATE_SUB(pd.dia, INTERVAL 30 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)
  GROUP BY 1, 2
),

compras AS (
  SELECT LOWER(c.nm_email) AS email, DATE(t.dt_ordered_at) AS dia_compra
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) BETWEEN '2026-04-09' AND '2026-09-01'
),

base AS (
  SELECT pd.email, pd.dia,
    IF(pd.eh_freemium = 1, 'freemium', 'membro') AS status,
    CASE WHEN pd.viu_sabatina = 1 THEN 'sabatina'
         WHEN pd.viu_top = 1 THEN 'top_playlist' ELSE 'outro' END AS grupo,
    CASE WHEN e.dias_ativos_30d <= 2 THEN '1_leve'
         WHEN e.dias_ativos_30d <= 8 THEN '2_medio' ELSE '3_heavy' END AS faixa_engaj,
    COUNTIF(c.dia_compra BETWEEN DATE_SUB(pd.dia, INTERVAL 60 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)) AS compra_60d_antes,
    COUNTIF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS pos14,
    COUNTIF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 30 DAY)) AS pos30,
    COUNTIF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 60 DAY)) AS pos60
  FROM pessoa_dia pd
  JOIN engaj e USING (email, dia)
  LEFT JOIN compras c ON c.email = pd.email
   AND c.dia_compra BETWEEN DATE_SUB(pd.dia, INTERVAL 60 DAY) AND DATE_ADD(pd.dia, INTERVAL 60 DAY)
  WHERE e.dias_ativos_30d >= 1
  GROUP BY 1, 2, 3, 4, 5
),

pessoa AS (
  SELECT status, faixa_engaj, grupo, email, COUNT(*) AS n_i,
         COUNTIF(pos14 > 0) AS y14, COUNTIF(pos30 > 0) AS y30, COUNTIF(pos60 > 0) AS y60
  FROM base WHERE compra_60d_antes = 0
  GROUP BY 1, 2, 3, 4
),

grp AS (
  SELECT status, faixa_engaj, grupo, SUM(n_i) AS pessoa_dias, COUNT(*) AS pessoas,
         SUM(y14) AS c14, SUM(y30) AS c30, SUM(y60) AS c60,
         SAFE_DIVIDE(SUM(y14), SUM(n_i)) AS p14, SAFE_DIVIDE(SUM(y30), SUM(n_i)) AS p30,
         SAFE_DIVIDE(SUM(y60), SUM(n_i)) AS p60
  FROM pessoa GROUP BY 1, 2, 3
)

SELECT g.status, g.faixa_engaj, g.grupo, g.pessoa_dias, g.pessoas, g.c14, g.c30, g.c60,
       ROUND(SAFE_DIVIDE(SUM(POW(p.y14 - g.p14 * p.n_i, 2)) / POW(g.pessoa_dias, 2), g.p14 * (1 - g.p14) / g.pessoa_dias), 3) AS deff14,
       ROUND(SAFE_DIVIDE(SUM(POW(p.y30 - g.p30 * p.n_i, 2)) / POW(g.pessoa_dias, 2), g.p30 * (1 - g.p30) / g.pessoa_dias), 3) AS deff30,
       ROUND(SAFE_DIVIDE(SUM(POW(p.y60 - g.p60 * p.n_i, 2)) / POW(g.pessoa_dias, 2), g.p60 * (1 - g.p60) / g.pessoa_dias), 3) AS deff60,
       ROUND(g.pessoa_dias / g.pessoas, 3) AS pd_por_pessoa
FROM pessoa p JOIN grp g USING (status, faixa_engaj, grupo)
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, g.p14, g.p30, g.p60
ORDER BY 1, 2, 3
