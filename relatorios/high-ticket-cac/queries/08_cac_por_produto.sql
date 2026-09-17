-- High-ticket: o que foi vendido em cada campanha e o CAC de cada família de produto.
--
-- MOTIVO (apontado pelo André, 17/09): o CAC blendado da campanha divide a verba por TODOS os
-- compradores da janela, e as promoções vendem várias coisas ao mesmo tempo — no BNO24, 10.684
-- dos 29.313 compradores levaram assinatura de ~R$ 205, não vitalício. Comparar "o CAC do
-- vitalício" entre campanhas exige separar o que foi vendido.
--
-- ⚠️ QUALQUER RATEIO AQUI É UMA ESCOLHA, NÃO UM DADO. A mídia dessas campanhas não é
--    product-specific: os anúncios do BNO24 são `[BNO24] [VENDA] [MEMBROS] ABO Monster`, sem
--    produto no nome. Não existe verba "do vitalício" para medir. Por isso a query devolve as
--    DUAS convenções possíveis e o relatório mostra as duas:
--
--      rateio por RECEITA    — custo_familia = verba × (receita da família ÷ receita total).
--                              Assume que a campanha vale o que fatura: produto caro carrega
--                              mais custo. É o rateio mais usado em P&L.
--      rateio por COMPRADOR  — custo por comprador é igual para todos (= CAC blendado).
--                              Assume que o anúncio custa o mesmo para trazer qualquer pessoa,
--                              e a diferença de ticket é mérito da oferta, não da mídia.
--
--    O intervalo entre as duas é a margem de erro honesta do "CAC do vitalício". Se a conclusão
--    muda de sinal entre os dois rateios, ela não está sustentada pelos dados.
--
-- ⚠️ CADA RATEIO TORNA UMA DAS MÉTRICAS CEGA, por construção:
--      por receita    -> o ROAS fica IGUAL para toda família (= ROAS da campanha); só o CAC separa.
--      por comprador  -> o CAC fica IGUAL para toda família (= CAC blendado); só o ROAS separa.
--    Nenhum dos dois ranqueia produtos pelas duas métricas ao mesmo tempo. Quem quiser uma
--    resposta única precisa de verba separada por produto na mídia — que hoje não existe
--    (os anúncios não trazem produto no nome).
--
-- Famílias pelo nm_plan_label do maior ticket do comprador (mesmo critério do universo).

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, r'\[TRA\]|TRAVESSIA'   AS rx, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', r'\[TRA\]|TRAVESSIA',                        2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', r'\[BNO24\]|\[BNO\]|BLACK',                  3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', r'\[BIT\]|NOVA MOEDA|BITCOIN',               4 UNION ALL
  SELECT 'BNO25',         DATE '2025-11-01', DATE '2025-11-30', r'\[BNO25\]|\[BNO\]|BLACK',                  5 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', r'\[DBI\]|BITCOIN',                          6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', r'\[CDL\]|CLUBE DO LIVRO',                   7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', r'\[BP10\]|10 ANOS|ANIVERS',                 8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', r'\[ODI\]|ODISSEIA',                         9
),

spend AS (
  SELECT dt, nm_campanha, vl_spend AS vl FROM `bp-staging.dbt_abe.tb_ht_meta_spend`
  UNION ALL
  SELECT reference_date, nm_campaign_name, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
  UNION ALL
  SELECT reference_date, nm_campaign_name, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
),

midia AS (
  SELECT w.sigla, SUM(s.vl) AS vl_midia
  FROM win AS w
  JOIN spend AS s
    ON s.dt BETWEEN w.dt_ini AND w.dt_fim
   AND REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx)
  GROUP BY 1
),

familia AS (
  SELECT
    sigla,
    CASE
      WHEN REGEXP_CONTAINS(LOWER(nm_plano_principal), r'vital|fundador')                       THEN 'Vitalício'
      WHEN REGEXP_CONTAINS(LOWER(nm_plano_principal), r'clube do livro|odisseia|cole')         THEN 'Livro / físico'
      WHEN REGEXP_CONTAINS(LOWER(nm_plano_principal),
             r'travessia|bitcoin|geopol|ci[eê]ncia|m[ée]todo|nova moeda')                      THEN 'Certificação'
      WHEN REGEXP_CONTAINS(LOWER(nm_plano_principal), r'mecenas')                              THEN 'Mecenas'
      WHEN REGEXP_CONTAINS(LOWER(nm_plano_principal), r'ebook|audiolivro|teller')              THEN 'Ebook / Teller'
      ELSE 'Assinatura recorrente'
    END AS nm_familia,
    COUNT(*)        AS qt_compradores,
    SUM(vl_receita) AS vl_receita
  FROM `bp-staging.dbt_abe.tb_ht_compradores`
  WHERE bl_universo_principal
  GROUP BY 1, 2
),

total AS (
  SELECT sigla, SUM(qt_compradores) AS qt_total, SUM(vl_receita) AS vl_total
  FROM familia GROUP BY 1
)

SELECT
  w.ord,
  f.sigla,
  f.nm_familia,
  f.qt_compradores,
  ROUND(f.vl_receita)                                              AS vl_receita,
  ROUND(f.vl_receita / f.qt_compradores)                           AS vl_ticket,
  ROUND(100 * f.qt_compradores / t.qt_total, 1)                    AS pct_compradores,
  ROUND(100 * f.vl_receita     / t.vl_total, 1)                    AS pct_receita,
  -- rateio por receita
  ROUND(m.vl_midia * f.vl_receita / t.vl_total)                    AS vl_custo_rateio_receita,
  ROUND(m.vl_midia * f.vl_receita / t.vl_total / f.qt_compradores, 2) AS vl_cac_rateio_receita,
  -- rateio por comprador (= CAC blendado da campanha, igual para toda família)
  ROUND(m.vl_midia / t.qt_total, 2)                                AS vl_cac_rateio_comprador,
  -- ⚠️ ROAS sob rateio por RECEITA é IDÊNTICO para toda família, por construção:
  --    receita ÷ (verba × receita/total) = total ÷ verba = ROAS da campanha. Não ranqueia nada.
  ROUND(t.vl_total / NULLIF(m.vl_midia, 0), 2)                     AS vl_roas_rateio_receita,
  -- Sob rateio por COMPRADOR o CAC é que fica igual, e o ROAS passa a diferenciar:
  --    receita ÷ (CAC blendado × compradores) = ticket ÷ CAC blendado.
  ROUND(f.vl_receita / NULLIF(m.vl_midia / t.qt_total * f.qt_compradores, 0), 2) AS vl_roas_rateio_comprador
FROM familia AS f
JOIN total AS t USING (sigla)
JOIN win   AS w USING (sigla)
LEFT JOIN midia AS m USING (sigla)
ORDER BY w.ord, f.vl_receita DESC;
