-- High-ticket: o esforço REAL do Comercial, normalizado por duração de campanha.
--
-- POR QUÊ ESTA QUERY EXISTE (correção de 21/09/2026): o relatório afirmava que o Comercial fazia
-- "metade das abordagens por dia" no BP10 contra o BNO24, e concluía daí que o time havia sido
-- desmobilizado. O André questionou a frase e ela não se sustenta.
--
-- A média diária realmente cai (5.228 → 2.806), mas só porque o BP10 durou 97 dias e o BNO24, 30.
-- Normalizando pela intensidade, o esforço é o MESMO:
--   · 30 dias mais intensos de cada: 5.228/dia (BNO24) × 5.378/dia (BP10)
--   · total de abordagens: 156.832 (BNO24) × 272.148 (BP10) — o BP10 abordou 74% MAIS
--   · pico diário: 7.496 (BNO24) × 11.267 (BP10)
--   · vendedores que abordaram: 67 × 71
--
-- ⚠️ NÃO calcular aqui a eficiência abordagem → venda para comparar campanhas: o numerador
--    (compradores do Comercial) depende do universo de atribuição, e as duas réguas DISCORDAM DE
--    SINAL — em `rastro` o BP10 sai 2,2× pior, em `janela` sai melhor. Sem régua comum não há
--    afirmação possível, e publicar uma das duas seria escolher o resultado.
--    O que é robusto é a taxa de RESPOSTA (medida dentro do próprio Zenvia, sem atribuição de
--    venda): 73,8% na Travessia → 43,8% no BNO24 → 36,9% no BP10 → 32,0% na Odisseia.

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS ini, DATE '2023-05-31' AS fim, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', 2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', 3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', 4 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', 6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', 7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', 8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', 9
),

dia AS (
  SELECT
    w.ord, w.sigla,
    DATE(a.dt_approach_start)    AS dt,
    COUNT(*)                     AS qt,
    COUNT(DISTINCT a.id_seller)  AS qt_vendedores_dia
  FROM win AS w
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_approaches` AS a
    ON DATE(a.dt_approach_start) BETWEEN w.ini AND w.fim
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_contacts` AS z USING (id_prospect)
  WHERE TRIM(z.nm_group) = 'Comercial'
  GROUP BY 1, 2, 3
),

-- intensidade comparável: os 30 dias mais movimentados de cada campanha
top30 AS (
  SELECT ord, sigla, qt
  FROM dia
  QUALIFY ROW_NUMBER() OVER (PARTITION BY sigla ORDER BY qt DESC) <= 30
)

SELECT
  d.ord,
  d.sigla,
  COUNT(*)                                    AS qt_dias_ativos,
  SUM(d.qt)                                   AS qt_abordagens_total,
  ROUND(AVG(d.qt))                            AS qt_abordagens_dia_media,
  MAX(d.qt)                                   AS qt_abordagens_pico,
  (SELECT ROUND(AVG(qt)) FROM top30 t WHERE t.sigla = d.sigla) AS qt_abordagens_dia_top30,
  MAX(d.qt_vendedores_dia)                    AS qt_vendedores_pico_dia
FROM dia AS d
GROUP BY d.ord, d.sigla
ORDER BY d.ord;
