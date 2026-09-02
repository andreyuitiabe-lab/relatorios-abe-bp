-- TESTE INDIVIDUAL v2 — desenho pessoa-dia (controla dia = campanha, spend, sazonalidade)
-- Para cada pessoa-dia com sessão ≥5min: assistiu sabatina ("BP nas Eleições") ou outro conteúdo?
-- Outcome: compra aprovada em D..D+14. Estratos: status (freemium/membro/ex) × faixa de engajamento.
-- Janela: 01/03–07/08/2026 (14d de maturação), playlist ativa desde antes.
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

pessoa_dia AS (
  SELECT
    email,
    dia,
    MAX(IF(nm_playlist = 'BP nas Eleições', 1, 0)) AS viu_sabatina,
    MAX(IF(nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium,
    SUM(seg) / 3600 AS horas_dia
  FROM sessoes
  GROUP BY 1, 2
),

-- engajamento prévio (30d antes) para pareamento; evita usar o próprio dia
engaj AS (
  SELECT
    pd.email, pd.dia,
    COUNT(DISTINCT s.dia) AS dias_ativos_30d
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
    pd.email, pd.dia, pd.viu_sabatina, pd.eh_freemium,
    CASE WHEN e.dias_ativos_30d = 0 THEN '0_novo'
         WHEN e.dias_ativos_30d <= 2 THEN '1_leve'
         WHEN e.dias_ativos_30d <= 8 THEN '2_medio'
         ELSE '3_heavy' END AS faixa_engaj,
    (SELECT COUNT(*) FROM compras c
      WHERE c.email = pd.email AND c.dia_compra BETWEEN pd.dia AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS n_compras,
    (SELECT SUM(c.vl) FROM compras c
      WHERE c.email = pd.email AND c.dia_compra BETWEEN pd.dia AND DATE_ADD(pd.dia, INTERVAL 14 DAY)) AS receita
  FROM pessoa_dia pd
  JOIN engaj e USING (email, dia)
)

SELECT
  IF(eh_freemium = 1, 'freemium', 'membro') AS status,
  faixa_engaj,
  viu_sabatina,
  COUNT(*) AS pessoa_dias,
  COUNTIF(n_compras > 0) AS com_compra_14d,
  ROUND(100 * COUNTIF(n_compras > 0) / COUNT(*), 3) AS tx_compra_pct,
  ROUND(SUM(COALESCE(receita, 0)) / COUNT(*), 2) AS receita_por_pessoa_dia
FROM base
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
