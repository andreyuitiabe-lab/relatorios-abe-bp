-- MÉTRICA PROPOSTA — IAC (Índice de Ativação Comercial do conteúdo)
-- Para cada playlist: entre membros de engajamento leve/médio SEM compra nos 60d anteriores,
-- qual a taxa de compra e a receita por pessoa-dia nos 14 dias seguintes ao consumo.
-- IAC = RPP-14 da playlist ÷ RPP-14 mediano do catálogo. Acompanhável mensalmente.
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_playlist, nm_plan,
         vl_watch_time_seconds AS seg
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    AND nm_playlist IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-03-01' AND '2026-08-07'
),

pessoa_dia_playlist AS (
  SELECT email, dia, nm_playlist,
         MAX(IF(nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium
  FROM sessoes GROUP BY 1, 2, 3
),

engaj AS (
  SELECT pd.email, pd.dia, COUNT(DISTINCT s.dia) AS dias_ativos_30d
  FROM (SELECT DISTINCT email, dia FROM pessoa_dia_playlist) pd
  LEFT JOIN sessoes s ON s.email = pd.email
   AND s.dia BETWEEN DATE_SUB(pd.dia, INTERVAL 30 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)
  GROUP BY 1, 2
),

compras AS (
  SELECT LOWER(c.nm_email) AS email, DATE(t.dt_ordered_at) AS dia_compra, t.vl_payment_gross AS vl
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) BETWEEN '2025-12-01' AND '2026-08-21'
),

base AS (
  SELECT p.nm_playlist, p.email, p.dia,
    (SELECT COUNT(*) FROM compras c WHERE c.email = p.email
       AND c.dia_compra BETWEEN DATE_ADD(p.dia, INTERVAL 1 DAY) AND DATE_ADD(p.dia, INTERVAL 14 DAY)) AS pos,
    (SELECT SUM(c.vl) FROM compras c WHERE c.email = p.email
       AND c.dia_compra BETWEEN DATE_ADD(p.dia, INTERVAL 1 DAY) AND DATE_ADD(p.dia, INTERVAL 14 DAY)) AS receita,
    (SELECT COUNT(*) FROM compras c WHERE c.email = p.email
       AND c.dia_compra BETWEEN DATE_SUB(p.dia, INTERVAL 60 DAY) AND DATE_SUB(p.dia, INTERVAL 1 DAY)) AS compra_60d
  FROM pessoa_dia_playlist p
  JOIN engaj e USING (email, dia)
  WHERE p.eh_freemium = 0            -- membros (o público onde o efeito existe)
    AND e.dias_ativos_30d BETWEEN 1 AND 8  -- engajamento leve/médio (heavy está no teto)
)

SELECT
  nm_playlist,
  COUNT(*) AS pessoa_dias,
  COUNTIF(pos > 0) AS com_compra_d1_d14,
  ROUND(100 * COUNTIF(pos > 0) / COUNT(*), 3) AS tx_compra_pct,
  ROUND(SUM(COALESCE(receita, 0)) / COUNT(*), 2) AS rpp14
FROM base
WHERE compra_60d = 0
GROUP BY 1
HAVING pessoa_dias >= 500
ORDER BY rpp14 DESC
