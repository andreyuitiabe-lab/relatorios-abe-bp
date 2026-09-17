-- RODADA 9a (auditoria) — erro-padrão CLUSTERIZADO POR PESSOA para o teste principal (query 14).
-- O Fisher da query 14 trata cada pessoa-dia como independente; a mesma pessoa aparece em
-- vários dias e as janelas D+1..D+14 de dias vizinhos se sobrepõem quase inteiras.
-- Aqui: mesma população, estratos e desfecho da query 14, agregados por PESSOA dentro de cada
-- grupo, com a soma de quadrados por cluster que dá a variância robusta de p̂:
--   Var_robusta(p̂) = Σ_i (y_i − p̂·n_i)² / N²      (i = pessoa; n_i pessoa-dias; y_i pessoa-dias com compra)
--   Var_naive(p̂)   = p̂(1−p̂)/N                     → DEFF = robusta ÷ naive
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_playlist, nm_plan
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-03-01' AND '2026-08-07'
),

top_playlists AS (
  SELECT nm_playlist FROM sessoes
  WHERE nm_playlist IS NOT NULL AND nm_playlist != 'BP nas Eleições'
  GROUP BY 1 ORDER BY COUNT(DISTINCT email) DESC LIMIT 8
),

pessoa_dia AS (
  SELECT s.email, s.dia,
    MAX(IF(s.nm_playlist = 'BP nas Eleições', 1, 0)) AS viu_sabatina,
    MAX(IF(s.nm_playlist IN (SELECT nm_playlist FROM top_playlists), 1, 0)) AS viu_top,
    MAX(IF(s.nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium
  FROM sessoes s GROUP BY 1, 2
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
    AND DATE(t.dt_ordered_at) BETWEEN '2025-12-01' AND '2026-08-21'
),

base AS (
  SELECT pd.email, pd.dia,
    IF(pd.eh_freemium = 1, 'freemium', 'membro') AS status,
    CASE WHEN pd.viu_sabatina = 1 THEN 'sabatina'
         WHEN pd.viu_top = 1 THEN 'top_playlist' ELSE 'outro' END AS grupo,
    CASE WHEN e.dias_ativos_30d <= 2 THEN '1_leve'
         WHEN e.dias_ativos_30d <= 8 THEN '2_medio' ELSE '3_heavy' END AS faixa_engaj,
    (SELECT COUNT(*) FROM compras c WHERE c.email = pd.email
       AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS pos,
    (SELECT COUNT(*) FROM compras c WHERE c.email = pd.email
       AND c.dia_compra BETWEEN DATE_SUB(pd.dia, INTERVAL 60 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)) AS compra_60d_antes
  FROM pessoa_dia pd
  JOIN engaj e USING (email, dia)
  WHERE e.dias_ativos_30d >= 1
),

pessoa AS (  -- cluster = pessoa dentro de (status, faixa, grupo)
  SELECT status, faixa_engaj, grupo, email,
         COUNT(*) AS n_i, COUNTIF(pos > 0) AS y_i
  FROM base
  WHERE compra_60d_antes = 0
  GROUP BY 1, 2, 3, 4
),

grp AS (
  SELECT status, faixa_engaj, grupo,
         SUM(n_i) AS pessoa_dias, COUNT(*) AS pessoas, SUM(y_i) AS com_compra,
         SAFE_DIVIDE(SUM(y_i), SUM(n_i)) AS p_hat
  FROM pessoa GROUP BY 1, 2, 3
)

SELECT g.status, g.faixa_engaj, g.grupo, g.pessoa_dias, g.pessoas, g.com_compra,
       ROUND(100 * g.p_hat, 3) AS tx_compra_pct,
       ROUND(SUM(POW(p.y_i - g.p_hat * p.n_i, 2)), 4) AS ss_cluster,
       ROUND(g.p_hat * (1 - g.p_hat) / g.pessoa_dias, 12) AS var_naive,
       ROUND(SUM(POW(p.y_i - g.p_hat * p.n_i, 2)) / POW(g.pessoa_dias, 2), 12) AS var_robusta,
       ROUND(SAFE_DIVIDE(SUM(POW(p.y_i - g.p_hat * p.n_i, 2)) / POW(g.pessoa_dias, 2),
                         g.p_hat * (1 - g.p_hat) / g.pessoa_dias), 3) AS deff,
       ROUND(g.pessoa_dias / g.pessoas, 3) AS pd_por_pessoa
FROM pessoa p
JOIN grp g USING (status, faixa_engaj, grupo)
GROUP BY 1, 2, 3, 4, 5, 6, 7, 9, g.p_hat
ORDER BY 1, 2, 3
