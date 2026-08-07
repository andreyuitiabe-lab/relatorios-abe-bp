-- Três recortes para direcionamento de mídia: sazonalidade, geografia e janela pós-compra.
-- Rodar os blocos separadamente (estão juntos por serem do mesmo tema).

-- ── 1. Sazonalidade: em que mês as pessoas doam ──────────────────────────────
-- Achado: nov+dez = 4% do ano (vs 8,3% esperado). Black Friday e Natal canibalizam.
-- Mas o ticket sobe em nov (R$ 6.660, o maior) — janela para o Comercial, não para volume.
WITH doacoes AS (
  SELECT
    EXTRACT(MONTH FROM t.dt_ordered_at) AS mes,
    t.vl_payment_gross AS vl
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.nm_status = 'approved'
    AND ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
      OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump%'
    AND t.vl_payment_gross >= 300
    AND DATE(t.dt_ordered_at) BETWEEN '2023-01-01' AND '2026-07-31'
)

SELECT
  mes,
  COUNT(*) AS doacoes,
  ROUND(SUM(vl)) AS receita,
  ROUND(AVG(vl)) AS ticket,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pc_do_ano
FROM doacoes
GROUP BY 1
ORDER BY 1;


-- ── 2. Geografia: propensão por UF ───────────────────────────────────────────
-- Achado: DF lidera (1,67x); SP tem a maior doação média (R$ 6.564); Nordeste < 0,7x.
WITH pessoa_uf AS (
  SELECT
    b.bl_is_mecenas,
    b.vl_total_mecenas,
    m.uf
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base` b
  JOIN `bp-staging.dbt_abe.tb_mecenas_person_map` m USING (id_person)
  WHERE m.uf IS NOT NULL AND LENGTH(m.uf) = 2
  QUALIFY ROW_NUMBER() OVER (PARTITION BY b.id_person ORDER BY m.id_gateway_customer) = 1
),

base AS (SELECT COUNT(*) AS bn, COUNTIF(bl_is_mecenas) AS bm FROM pessoa_uf)

SELECT
  uf,
  COUNT(*) AS pessoas,
  COUNTIF(bl_is_mecenas) AS doadores,
  ROUND(100 * COUNTIF(bl_is_mecenas) / COUNT(*), 2) AS pc_conv,
  ROUND((COUNTIF(bl_is_mecenas) / COUNT(*)) / (base.bm / base.bn), 2) AS lift,
  ROUND(AVG(IF(bl_is_mecenas, vl_total_mecenas, NULL))) AS doacao_media
FROM pessoa_uf
CROSS JOIN base
GROUP BY uf, base.bn, base.bm
HAVING pessoas >= 5000
ORDER BY lift DESC;


-- ── 3. Janela: quanto tempo depois da última compra a pessoa doa ─────────────
-- Achado: só 13% doam em até 30 dias. 40% doam 6-12 meses depois (ciclo anual).
-- Implicação: mirar quem comprou há 6-12 meses, não quem acabou de comprar.
WITH mec AS (
  SELECT
    m.id_person,
    MIN(t.dt_ordered_at) AS dt_doacao
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-staging.dbt_abe.tb_mecenas_person_map` m
    ON m.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
    AND ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
      OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump%'
    AND t.vl_payment_gross >= 300
  GROUP BY 1
),

anterior AS (
  SELECT
    m.id_person,
    m.dt_doacao,
    MAX(t.dt_ordered_at) AS dt_compra_anterior
  FROM mec m
  JOIN `bp-staging.dbt_abe.tb_mecenas_person_map` pm USING (id_person)
  JOIN `bp-datawarehouse.masterdata.fct_transactions` t
    ON t.id_gateway_customer = pm.id_gateway_customer
  WHERE t.nm_status = 'approved'
    AND t.dt_ordered_at < m.dt_doacao
    -- exclui doações Mecenas anteriores: a janela é desde a última compra COMUM
    AND NOT (
      ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
        OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
      AND t.vl_payment_gross >= 300
    )
  GROUP BY 1, 2
)

SELECT
  CASE WHEN d <= 7 THEN 'a. ate 7 dias'
       WHEN d <= 30 THEN 'b. 8-30 dias'
       WHEN d <= 90 THEN 'c. 31-90 dias'
       WHEN d <= 180 THEN 'd. 91-180 dias'
       WHEN d <= 365 THEN 'e. 6-12 meses'
       ELSE 'f. mais de 1 ano' END AS janela,
  COUNT(*) AS doadores,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pc
FROM (SELECT DATE_DIFF(DATE(dt_doacao), DATE(dt_compra_anterior), DAY) AS d FROM anterior)
GROUP BY 1
ORDER BY 1
