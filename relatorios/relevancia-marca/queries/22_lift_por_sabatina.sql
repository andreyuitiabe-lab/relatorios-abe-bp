-- TESTE A (formato vs pauta) — máquina da query 14 POR SABATINA INDIVIDUAL.
-- População: pessoa-dia de MEMBRO (nenhuma sessão free/fake-free no dia), engajamento
-- leve/médio (1–8 dias ativos nos 30d anteriores), SEM compra aprovada não-renovação
-- nos 60 dias anteriores. Desfechos: compra aprovada não-renovação em D+1..D+7 e D+1..D+14.
-- Comparador: top-8 playlists por audiência na janela (excl. BP nas Eleições e BP Entrevista,
-- para não contaminar o contraste de formato). Saída granular por (grupo, dia) para o
-- pareamento por calendário ser feito na análise (controle restrito aos dias de cada sabatina).
-- Janela de pessoa-dias: 08/06/2026 (estreia Caiado) a 25/08/2026 (D+7 completo com compras
-- até 01/09; D+14 completo só para dia <= 18/08 — Renan/Marçal, estreia 19/08, ficam fora do D+14).
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_playlist, nm_media, nm_plan
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-05-01' AND '2026-08-25'  -- 05-01 p/ lookback de engajamento
),

janela AS (
  SELECT * FROM sessoes WHERE dia BETWEEN '2026-06-08' AND '2026-08-25'
),

top_playlists AS (
  SELECT nm_playlist FROM janela
  WHERE nm_playlist IS NOT NULL
    AND nm_playlist NOT IN ('BP nas Eleições', 'BP Entrevista')
  GROUP BY 1 ORDER BY COUNT(DISTINCT email) DESC LIMIT 8
),

pessoa_dia AS (
  SELECT email, dia,
    MAX(IF(nm_playlist = 'BP nas Eleições', 1, 0)) AS viu_sabatina,
    MAX(IF(nm_playlist IN (SELECT nm_playlist FROM top_playlists), 1, 0)) AS viu_top,
    MAX(IF(nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium
  FROM janela GROUP BY 1, 2
),

sabatina_media AS (  -- pessoa-dia × sabatina assistida (raro assistir 2 no mesmo dia; conta nas duas)
  SELECT DISTINCT email, dia, nm_media
  FROM janela WHERE nm_playlist = 'BP nas Eleições'
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
    AND DATE(t.dt_ordered_at) BETWEEN '2026-04-01' AND '2026-09-01'  -- 01/09 = último dia completo
),

base AS (
  SELECT pd.email, pd.dia, pd.viu_sabatina, pd.viu_top,
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
    AND e.dias_ativos_30d BETWEEN 1 AND 8   -- leve/médio (heavy está no teto)
)

SELECT sm.nm_media AS grupo, b.dia,
  COUNT(*) AS pessoa_dias,
  COUNTIF(b.pos7 > 0) AS com_compra_d7,
  COUNTIF(b.pos14 > 0) AS com_compra_d14,
  ROUND(SUM(COALESCE(b.receita7, 0)), 2) AS receita_d7,
  ROUND(SUM(COALESCE(b.receita14, 0)), 2) AS receita_d14
FROM base b
JOIN sabatina_media sm USING (email, dia)
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
WHERE compra_60d = 0 AND viu_sabatina = 0 AND viu_top = 1
GROUP BY 1, 2
ORDER BY 1, 2
