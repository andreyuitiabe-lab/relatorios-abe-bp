-- TESTE B (médio prazo) — Q26: sensibilidade com o desenho ORIGINAL da query 14
-- (pessoa-dias desde 2026-03-01, comparadores incluindo mar–jun sem sabatina no ar),
-- mas com o mesmo cutoff de censura da Q25: dia <= 2026-07-03 (D+60 completo para todos).
-- Serve para (a) checar se o D+14 reproduz a magnitude do achado §3 da ANALISE.md e
-- (b) testar se a curva do lift por janela é robusta ao calendário do comparador.
-- Top-8 playlists medidas no período todo (como na query 14).
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_playlist, nm_plan,
         vl_watch_time_seconds AS seg
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-01-30' AND '2026-07-03'
),

top_playlists AS (
  SELECT nm_playlist FROM sessoes
  WHERE nm_playlist IS NOT NULL AND nm_playlist != 'BP nas Eleições'
    AND dia BETWEEN '2026-03-01' AND '2026-07-03'
  GROUP BY 1 ORDER BY COUNT(DISTINCT email) DESC LIMIT 8
),

pessoa_dia AS (
  SELECT s.email, s.dia,
    MAX(IF(s.nm_playlist = 'BP nas Eleições', 1, 0)) AS viu_sabatina,
    MAX(IF(s.nm_playlist IN (SELECT nm_playlist FROM top_playlists), 1, 0)) AS viu_top,
    MAX(IF(s.nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium
  FROM sessoes s
  WHERE s.dia BETWEEN '2026-03-01' AND '2026-07-03'
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
  SELECT LOWER(c.nm_email) AS email, DATE(t.dt_ordered_at) AS dia_compra,
         t.vl_payment_gross AS vl
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) BETWEEN '2025-12-31' AND '2026-09-01'
),

base AS (
  SELECT pd.email, pd.dia, pd.eh_freemium,
    CASE WHEN pd.viu_sabatina = 1 THEN 'sabatina'
         WHEN pd.viu_top = 1 THEN 'top_playlist' ELSE 'outro' END AS grupo,
    CASE WHEN e.dias_ativos_30d <= 2 THEN '1_leve'
         WHEN e.dias_ativos_30d <= 8 THEN '2_medio' ELSE '3_heavy' END AS faixa_engaj,
    COUNTIF(c.dia_compra BETWEEN DATE_SUB(pd.dia, INTERVAL 60 DAY)
                             AND DATE_SUB(pd.dia, INTERVAL 1 DAY)) AS compra_60d_antes,
    COUNTIF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY)
                             AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS pos14,
    COUNTIF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY)
                             AND DATE_ADD(pd.dia, INTERVAL 30 DAY)) AS pos30,
    COUNTIF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY)
                             AND DATE_ADD(pd.dia, INTERVAL 60 DAY)) AS pos60,
    SUM(IF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY)
                            AND DATE_ADD(pd.dia, INTERVAL 14 DAY), c.vl, 0)) AS rec14,
    SUM(IF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY)
                            AND DATE_ADD(pd.dia, INTERVAL 30 DAY), c.vl, 0)) AS rec30,
    SUM(IF(c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY)
                            AND DATE_ADD(pd.dia, INTERVAL 60 DAY), c.vl, 0)) AS rec60
  FROM pessoa_dia pd
  JOIN engaj e USING (email, dia)
  LEFT JOIN compras c ON c.email = pd.email
   AND c.dia_compra BETWEEN DATE_SUB(pd.dia, INTERVAL 60 DAY)
                        AND DATE_ADD(pd.dia, INTERVAL 60 DAY)
  WHERE e.dias_ativos_30d >= 1
  GROUP BY 1, 2, 3, 4, 5
)

SELECT
  IF(eh_freemium = 1, 'freemium', 'membro') AS status,
  faixa_engaj, grupo,
  COUNT(*) AS pessoa_dias,
  COUNTIF(pos14 > 0) AS conv_d14,
  COUNTIF(pos30 > 0) AS conv_d30,
  COUNTIF(pos60 > 0) AS conv_d60,
  ROUND(SUM(COALESCE(rec14, 0)), 2) AS receita_d14,
  ROUND(SUM(COALESCE(rec30, 0)), 2) AS receita_d30,
  ROUND(SUM(COALESCE(rec60, 0)), 2) AS receita_d60
FROM base
WHERE compra_60d_antes = 0
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
