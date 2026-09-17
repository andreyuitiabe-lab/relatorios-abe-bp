-- High-ticket: saturação da base e esgotamento da demanda reprimida.
--
-- Responde as duas perguntas de fundo:
--   (a) o público está saturando? -> penetração acumulada de high-ticket na base elegível
--       e taxa de conversão da base disponível em cada campanha
--   (b) era demanda reprimida que está acabando? -> % de compradores em PRIMEIRA compra
--       high-ticket, tempo desde a compra anterior e tenure de quem compra
--
-- Base elegível de cada campanha = pessoas com membership ativa no dia da abertura
-- (whitelist de membership — ver 01_universo_compradores.sql), separando quem já tinha
-- comprado high-ticket (> R$ 1.000) antes e quem não tinha.
-- A taxa de penetração usa como denominador quem AINDA NÃO tinha high-ticket: é o
-- estoque de demanda reprimida disponível para a campanha vender.

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', 2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', 3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', 4 UNION ALL
  SELECT 'BNO25',         DATE '2025-11-01', 5 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', 6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', 7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', 8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', 9
),

subs AS (
  SELECT
    LOWER(TRIM(u.nm_email)) AS nm_email,
    s.dt_started_at,
    s.dt_expires_in
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` AS s
  JOIN `bp-datawarehouse.masterdata.dim_user` AS u ON s.id_user = u.id_user
  WHERE s.nm_type = 'paid'
    AND u.nm_email IS NOT NULL
    AND (
      REGEXP_CONTAINS(LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)),
        r'^(bp-)?(good|better|best|black|supporter|mecenas|intermediario|premium|essencial|economico|basico|apoiador|originais|fraterno|patriota|bp-select|combo-liberdade)')
      OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'combo-religioso%'
      OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'combo-essencial%'
      OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'extensao-assinatura-%'
      OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'bolsa-mecenas%'
    )
    AND LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) <> 'essencial-estudar-bem'
),

-- membership ativa na abertura da campanha + tenure
base AS (
  SELECT
    w.sigla,
    s.nm_email,
    MIN(DATE(s.dt_started_at)) AS dt_primeira_assinatura
  FROM win AS w
  JOIN subs AS s
    ON DATE(s.dt_started_at) <= w.dt_ini
   AND DATE(s.dt_expires_in) >= w.dt_ini
  GROUP BY 1, 2
),

-- quem já tinha comprado high-ticket antes da abertura
ht_previo AS (
  SELECT
    w.sigla,
    LOWER(TRIM(c.nm_email)) AS nm_email
  FROM win AS w
  JOIN `bp-datawarehouse.masterdata.fct_transactions` AS t
    ON DATE(t.dt_ordered_at) < w.dt_ini
   AND t.nm_status = 'approved'
   AND t.vl_payment_gross > 1000
  JOIN `bp-datawarehouse.masterdata.dim_contact` AS c USING (id_gateway_customer)
  WHERE c.nm_email IS NOT NULL
  GROUP BY 1, 2
),

base_class AS (
  SELECT
    b.sigla,
    b.nm_email,
    b.dt_primeira_assinatura,
    h.nm_email IS NOT NULL AS bl_ja_tinha_ht
  FROM base AS b
  LEFT JOIN ht_previo AS h USING (sigla, nm_email)
),

agg_base AS (
  SELECT
    sigla,
    COUNT(*)                        AS qt_base_ativa,
    COUNTIF(NOT bl_ja_tinha_ht)     AS qt_base_sem_ht,
    COUNTIF(bl_ja_tinha_ht)         AS qt_base_com_ht
  FROM base_class
  GROUP BY 1
),

-- compradores da campanha (universo principal)
comp AS (
  SELECT
    c.sigla,
    COUNT(*)                                          AS qt_compradores,
    COUNTIF(NOT c.bl_ht_previo)                       AS qt_primeira_ht,
    COUNTIF(c.st_status_compra = 'membro' AND NOT c.bl_ht_previo) AS qt_membro_primeira_ht,
    ROUND(SUM(c.vl_receita))                          AS vl_receita,
    APPROX_QUANTILES(DATE_DIFF(DATE(c.dt_primeira_compra),
                               DATE(c.dt_ultima_compra_previa), DAY), 2)[OFFSET(1)] AS qt_dias_desde_compra_mediana,
    ROUND(AVG(c.vl_gasto_previo))                     AS vl_gasto_previo_medio
  FROM `bp-staging.dbt_abe.tb_ht_compradores` AS c
  WHERE c.bl_universo_principal
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  w.dt_ini,
  b.qt_base_ativa,
  b.qt_base_sem_ht,
  ROUND(100 * b.qt_base_com_ht / b.qt_base_ativa, 1) AS pct_base_ja_com_ht,
  c.qt_compradores,
  c.qt_primeira_ht,
  ROUND(100 * c.qt_primeira_ht / c.qt_compradores, 1) AS pct_compradores_primeira_ht,
  -- penetração: quanto do estoque de demanda reprimida a campanha converteu
  ROUND(100 * c.qt_membro_primeira_ht / NULLIF(b.qt_base_sem_ht, 0), 3) AS pct_penetracao_estoque,
  c.qt_dias_desde_compra_mediana,
  c.vl_gasto_previo_medio,
  c.vl_receita
FROM win AS w
LEFT JOIN agg_base AS b USING (sigla)
LEFT JOIN comp     AS c USING (sigla)
ORDER BY w.ord;
