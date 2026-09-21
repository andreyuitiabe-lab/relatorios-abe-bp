-- High-ticket: CAC separado por FAIXA DE VALOR DA VENDA.
--
-- PEDIDO DO ANDRÉ (repetido em 17 e 18/09): o CAC blendado de uma campanha mistura quem pagou
-- R$ 7,90 com quem pagou R$ 3.484, e isso torna o número sem sentido para decidir qualquer coisa.
-- No BNO25, 94% dos compradores levaram produto de entrada — o CAC de R$ 104 descreve a captação
-- barata, não o vitalício.
--
-- Faixas (pelo maior ticket que o comprador pagou na campanha):
--   alto    > R$ 1.000   — 46% dos compradores, 88% da receita
--   médio   R$ 200–1.000 — 25% / 8%
--   entrada < R$ 200     — 29% / 4%
--
-- Rateio da verba: POR RECEITA (convenção oficial, decisão do André em 17/09).
--   custo_faixa = verba × (receita da faixa ÷ receita total da campanha)
--
-- ⚠️ O rateio é escolha, não dado: a mídia não é comprada por faixa de preço. E esta convenção
--    torna o ROAS idêntico em todas as faixas por construção (receita ÷ [verba × receita/total]
--    = ROAS da campanha) — só o CAC diferencia. Por isso a query devolve também o CAC sob rateio
--    por comprador, onde o oposto acontece.

WITH win AS (
  SELECT 'TRA'   AS sigla, 1 AS ord UNION ALL SELECT 'TRA2', 2 UNION ALL
  SELECT 'BNO24', 3 UNION ALL SELECT 'BIT',  4 UNION ALL
  SELECT 'DBI',   6 UNION ALL SELECT 'CDL',  7 UNION ALL SELECT 'BP10',  8 UNION ALL
  SELECT 'ODI',   9
),

faixa AS (
  SELECT
    sigla,
    CASE WHEN vl_maior_tx > 1000 THEN 'alto'
         WHEN vl_maior_tx >= 200 THEN 'medio'
         ELSE 'entrada' END              AS nm_faixa,
    COUNT(*)                             AS qt_compradores,
    SUM(vl_receita)                      AS vl_receita,
    AVG(vl_receita)                      AS vl_ticket,
    COUNTIF(st_status_compra = 'membro') AS qt_membro
  FROM `bp-staging.dbt_abe.tb_ht_compradores`
  WHERE bl_universo_principal
  GROUP BY 1, 2
),

total AS (
  SELECT sigla, SUM(qt_compradores) AS qt_total, SUM(vl_receita) AS vl_total
  FROM faixa GROUP BY 1
),

-- verba de mídia por campanha: a mesma do consolidado (tag), com a Travessia vindo da planilha
midia AS (
  SELECT 'TRA' AS sigla, 869815.77 AS vl_midia UNION ALL
  SELECT 'TRA2',  178663.00 UNION ALL SELECT 'BNO24', 5466226.02 UNION ALL
  SELECT 'BIT',  1282908.90 UNION ALL
  SELECT 'DBI',   170108.69 UNION ALL SELECT 'CDL',   5071111.74 UNION ALL
  SELECT 'BP10', 7938719.68 UNION ALL SELECT 'ODI',   1690931.03
)

SELECT
  w.ord,
  f.sigla,
  f.nm_faixa,
  f.qt_compradores,
  ROUND(f.vl_receita)                                                   AS vl_receita,
  ROUND(f.vl_ticket)                                                    AS vl_ticket,
  ROUND(100 * f.qt_compradores / t.qt_total, 1)                         AS pct_compradores,
  ROUND(100 * f.vl_receita     / t.vl_total, 1)                         AS pct_receita,
  ROUND(100 * f.qt_membro      / f.qt_compradores, 1)                   AS pct_membro,
  -- rateio oficial: por receita
  ROUND(m.vl_midia * f.vl_receita / t.vl_total)                         AS vl_custo_rateado,
  ROUND(m.vl_midia * f.vl_receita / t.vl_total / f.qt_compradores, 2)   AS vl_cac_faixa,
  -- sensibilidade: por comprador (aí o CAC fica igual em toda faixa e o ROAS é que separa)
  ROUND(m.vl_midia / t.qt_total, 2)                                     AS vl_cac_rateio_comprador,
  ROUND(f.vl_receita / NULLIF(m.vl_midia / t.qt_total * f.qt_compradores, 0), 2) AS vl_roas_rateio_comprador
FROM faixa AS f
JOIN total AS t USING (sigla)
JOIN win   AS w USING (sigla)
LEFT JOIN midia AS m USING (sigla)
ORDER BY w.ord, CASE f.nm_faixa WHEN 'alto' THEN 1 WHEN 'medio' THEN 2 ELSE 3 END;
