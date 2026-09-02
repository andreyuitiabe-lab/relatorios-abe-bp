-- TESTE INDIVIDUAL da hipótese "relevância baixa resistência na adesão"
-- Coorte: freemium com 1ª sessão ≥5min entre 01/06 e 07/08/2026 (14d de janela de conversão)
-- Tratamento = 1ª sessão do período foi numa sabatina (playlist "BP nas Eleições")
-- Controle  = 1ª sessão foi em outro conteúdo
-- Outcome  = compra aprovada nos 14 dias após a 1ª sessão
-- Pareamento por horas consumidas (proxy de engajamento — principal confundidor de seleção)
WITH sessoes AS (
  SELECT
    LOWER(nm_email) AS email,
    DATE(dt_created_at) AS dia,
    nm_playlist,
    vl_watch_time_seconds AS seg,
    nm_plan
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-06-01' AND '2026-08-07'
),

freemium AS (  -- só quem estava freemium em toda sessão do período (nunca aparece como pago)
  SELECT email
  FROM sessoes
  GROUP BY email
  HAVING COUNTIF(nm_plan NOT IN ('free', 'fake-free')) = 0
),

primeira AS (
  SELECT
    s.email,
    MIN(s.dia) AS dia_1a_sessao,
    ROUND(SUM(s.seg) / 3600, 2) AS horas_periodo,
    COUNT(DISTINCT s.dia) AS dias_ativos
  FROM sessoes s
  JOIN freemium f USING (email)
  GROUP BY 1
),

grupo AS (  -- conteúdo da 1ª sessão define o grupo
  SELECT
    p.email, p.dia_1a_sessao, p.horas_periodo, p.dias_ativos,
    MAX(IF(s.nm_playlist = 'BP nas Eleições', 1, 0)) AS tratado
  FROM primeira p
  JOIN sessoes s ON s.email = p.email AND s.dia = p.dia_1a_sessao
  GROUP BY 1, 2, 3, 4
),

compras AS (
  SELECT LOWER(c.nm_email) AS email, DATE(t.dt_ordered_at) AS dia_compra, t.vl_payment_gross
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) BETWEEN '2026-06-01' AND '2026-08-21'
)

SELECT
  g.tratado,
  CASE
    WHEN g.horas_periodo < 1 THEN '1_ate_1h'
    WHEN g.horas_periodo < 3 THEN '2_1a3h'
    WHEN g.horas_periodo < 10 THEN '3_3a10h'
    ELSE '4_10h_mais'
  END AS faixa_horas,
  COUNT(*) AS pessoas,
  COUNTIF(cp.email IS NOT NULL) AS compraram_14d,
  ROUND(100 * COUNTIF(cp.email IS NOT NULL) / COUNT(*), 3) AS tx_adesao_pct,
  ROUND(SUM(COALESCE(cp.receita, 0)) / COUNT(*), 2) AS receita_por_pessoa
FROM grupo g
LEFT JOIN (
  SELECT c.email, MIN(c.dia_compra) AS dia_compra, SUM(c.vl_payment_gross) AS receita
  FROM compras c
  JOIN grupo g2 ON g2.email = c.email
  WHERE c.dia_compra BETWEEN g2.dia_1a_sessao AND DATE_ADD(g2.dia_1a_sessao, INTERVAL 14 DAY)
  GROUP BY 1
) cp ON cp.email = g.email
GROUP BY 1, 2
ORDER BY 2, 1
