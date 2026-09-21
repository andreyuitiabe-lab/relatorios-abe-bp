-- High-ticket: RECEITA LÍQUIDA DE AQUISIÇÃO por campanha.
--
-- PEDIDO DO ANDRÉ (18/09): "fazíamos coisas que paramos e perdemos margem por isso?" — com o
-- escopo fechado depois: "eu preciso só dos custos de aquisição mesmo".
--
-- Receita líquida de aquisição = receita − mídia − comissão do Comercial − custo de disparo do CRM
--
-- 🚫 NÃO É MARGEM, e não deve ser chamada assim. Fora da conta, de propósito (escopo do pedido):
--    impostos e gateway (12–18%), reembolso (6,5%), custo de produto físico (15–25% em livro e
--    coleção), folha do Comercial e do time de mídia, produção de conteúdo.
--    Referência de margem de verdade: `relatorios/midia-paga/MARGEM.md` — 0,75 no digital, 0,55
--    no físico. Aplicando aqueles descontos, a Travessia sai de 83% para ~61% e o CDL de 80% para
--    ~38% (o CDL é livro físico). Se alguém precisar de margem, é aquele documento, não este.
--
-- O que ESTA métrica responde: quanto de cada real de receita a campanha entrega depois de pagar
-- para adquirir o comprador. É a métrica certa para comparar EFICIÊNCIA DE AQUISIÇÃO entre
-- campanhas — e é comparável entre elas porque os custos omitidos são proporcionais à receita.
--
-- ⚠️ A comissão de 9% é premissa do André (17/09) e é PISO do custo do Comercial.
-- ⚠️ A Travessia não tem custo de CRM (a Insider começa em 30/01/2024) — a contribuição dela
--    está levemente superestimada, mas o CRM é 1–3% da receita nas outras, então é ruído.

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, 'TRA'   AS tag, r'\[TRA\]|TRAVESSIA'          AS rx, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', 'TRA',   r'\[TRA\]|TRAVESSIA',                  2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', 'BNO24', r'\[BNO24\]|\[BNO\]|BLACK',            3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', 'BIT',   r'\[BIT\]|NOVA MOEDA|BITCOIN',         4 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', 'DBI',   r'\[DBI\]|BITCOIN',                    6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', 'CDL',   r'\[CDL\]|CLUBE DO LIVRO',             7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', 'BP10',  r'\[BP10\]|10 ANOS|ANIVERS',           8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', 'ODI',   r'\[ODI\]|ODISSEIA',                   9
),

comp AS (
  SELECT sigla, COUNT(*) AS qt_compradores, SUM(vl_receita) AS vl_receita,
         SUM(IF(nm_canal = 'comercial', vl_receita, 0)) AS vl_rec_comercial,
         COUNTIF(vl_maior_tx > 1000)                    AS qt_comp_ht,
         SUM(IF(vl_maior_tx > 1000, vl_receita, 0))     AS vl_rec_ht
  FROM `bp-staging.dbt_abe.tb_ht_compradores`
  WHERE bl_universo_principal GROUP BY 1
),

midia AS (
  SELECT 'TRA' AS sigla, 869815.77 AS vl_midia UNION ALL
  SELECT 'TRA2',  178663.00 UNION ALL SELECT 'BNO24', 5466226.02 UNION ALL
  SELECT 'BIT',  1282908.90 UNION ALL
  SELECT 'DBI',   170108.69 UNION ALL SELECT 'CDL',   5071111.74 UNION ALL
  SELECT 'BP10', 7938719.68 UNION ALL SELECT 'ODI',   1690931.03
),

crm AS (
  SELECT w.sigla,
    SUM(CASE i.nm_channel WHEN 'whatsapp' THEN i.qt_insider_delivered * 0.323
                          WHEN 'email'    THEN i.qt_insider_delivered * 0.0008
                          ELSE 0 END) AS vl_custo_crm
  FROM win AS w
  JOIN `bp-datawarehouse.datamart.dtm_analytics_revenue_insider_funnel` AS i
    ON i.dt_dispatch_date BETWEEN w.dt_ini AND w.dt_fim
   AND UPPER(i.nm_campaign_tag) = w.tag
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  c.qt_compradores,
  ROUND(c.vl_receita)                                     AS vl_receita,
  ROUND(m.vl_midia)                                       AS vl_midia,
  ROUND(c.vl_rec_comercial * 0.09)                        AS vl_comissao,
  ROUND(COALESCE(cr.vl_custo_crm, 0))                     AS vl_custo_crm,
  ROUND(m.vl_midia + c.vl_rec_comercial * 0.09 + COALESCE(cr.vl_custo_crm, 0)) AS vl_custo_aquisicao,
  ROUND(c.vl_receita - m.vl_midia - c.vl_rec_comercial * 0.09 - COALESCE(cr.vl_custo_crm, 0)) AS vl_contribuicao,
  ROUND(100 * (c.vl_receita - m.vl_midia - c.vl_rec_comercial * 0.09 - COALESCE(cr.vl_custo_crm, 0))
        / c.vl_receita, 1)                                AS pct_liquido_aquisicao,
  ROUND((c.vl_receita - m.vl_midia - c.vl_rec_comercial * 0.09 - COALESCE(cr.vl_custo_crm, 0))
        / c.qt_compradores)                               AS vl_liquido_por_comprador,
  -- quanto do custo de aquisição é mídia (o único que cresce com escala)
  ROUND(100 * m.vl_midia
        / (m.vl_midia + c.vl_rec_comercial * 0.09 + COALESCE(cr.vl_custo_crm, 0)), 1) AS pct_custo_midia
FROM win AS w
JOIN comp AS c USING (sigla)
JOIN midia AS m USING (sigla)
LEFT JOIN crm AS cr USING (sigla)
ORDER BY w.ord;
