-- TESTE B (médio prazo) — Q25: máquina da query 14 com janelas D+1..14 / D+1..30 / D+1..60
-- sobre o MESMO universo de pessoa-dias: dia ∈ [2026-06-08 (estreia da playlist),
-- 2026-07-03 (cutoff p/ D+60 completo com follow-up até 2026-09-01)].
-- Assim tratado e comparador compartilham o mesmo calendário e TODOS os pessoa-dias têm
-- as 3 janelas completas — as curvas entre janelas são comparáveis (nenhuma mistura de universo).
-- D+90 é infactível hoje (ver 24_censura_sabatinas.sql). Sobrevivem 6 sabatinas:
-- Caiado, Zema, Aldo Rebelo, Derrite, Salles, Cury.
-- Regras herdadas da query 14: sessão >= 300s; outcome nunca inclui D+0; compra = approved e
-- não-renovação, join por e-mail via dim_contact; exclusão de compra nos 60d anteriores;
-- estrato exige >= 1 dia ativo nos 30d anteriores; classificação por pessoa-DIA com
-- precedência sabatina > top_playlist > outro (a mesma pessoa pode aparecer em grupos
-- diferentes em dias diferentes — regra idêntica à query 14).
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_playlist, nm_plan,
         vl_watch_time_seconds AS seg
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    -- 30 dias antes do início do universo (para o engajamento prévio) até o fim do universo
    AND DATE(dt_created_at) BETWEEN '2026-05-09' AND '2026-07-03'
),

top_playlists AS (
  SELECT nm_playlist FROM sessoes
  WHERE nm_playlist IS NOT NULL AND nm_playlist != 'BP nas Eleições'
    AND dia BETWEEN '2026-06-08' AND '2026-07-03'   -- top-8 medidas no próprio universo
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
  SELECT LOWER(c.nm_email) AS email, DATE(t.dt_ordered_at) AS dia_compra,
         t.vl_payment_gross AS vl
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    -- 60d antes do início do universo até a última data completa de transação
    AND DATE(t.dt_ordered_at) BETWEEN '2026-04-09' AND '2026-09-01'
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
  WHERE e.dias_ativos_30d >= 1   -- exclui "sem atividade prévia"
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
WHERE compra_60d_antes = 0   -- controla "comprou recentemente"
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
