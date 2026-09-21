-- High-ticket: CAC por campanha e por canal.
--
-- CAC = mídia ÷ compradores da campanha (definição escolhida pelo André).
-- Duas leituras de mídia, porque as duas respondem perguntas diferentes:
--   _tag    — só a verba das campanhas de mídia que carregam a sigla no nome. É o CAC
--             atribuível ao lançamento. Subestima quando o lançamento também é vendido
--             por campanha genérica/perpétua (caso das promoções sitewide).
--   _janela — toda a verba da casa no período. É o CAC blended: o que a empresa gastou
--             em mídia enquanto aquela campanha estava no ar. Superestima quando havia
--             outra campanha grande rodando junto (BP10 × ODI × CBR em 2026).
-- O número honesto de cada campanha está entre os dois; o memo reporta os dois.
--
-- Fontes de mídia:
--   Meta   -> bp-staging.dbt_abe.tb_ht_meta_spend (Marketing API, desde 17/08/2023)
--   Google -> datamart.dtm_analytics_google_ads_funnel (desde jan/2025)
--   PMax   -> datamart.dtm_analytics_pmax_ads_funnel  (desde jan/2025)
-- ⚠️ TRA (abr–mai/2023) fica fora das três: custo só na planilha do time de tráfego.

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, r'\[TRA\]|TRAVESSIA'   AS rx, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', r'\[TRA\]|TRAVESSIA',                        2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', r'\[BNO24\]|\[BNO\]|BLACK',                  3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', r'\[BIT\]|NOVA MOEDA|BITCOIN',               4 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', r'\[DBI\]|BITCOIN',                          6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', r'\[CDL\]|CLUBE DO LIVRO',                   7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', r'\[BP10\]|10 ANOS|ANIVERS',                 8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', r'\[ODI\]|ODISSEIA',                         9
),

spend AS (
  SELECT 'meta' AS nm_fonte, dt, nm_campanha, id_campanha, vl_spend AS vl, qt_impressoes, qt_cliques
  FROM `bp-staging.dbt_abe.tb_ht_meta_spend`
  UNION ALL
  SELECT 'google', reference_date, nm_campaign_name, CAST(id_advertising AS STRING),
         vl_amount_spent, qt_impressions, qt_outbound_clicks
  FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
  UNION ALL
  SELECT 'pmax', reference_date, nm_campaign_name, CAST(id_campaign AS STRING),
         vl_amount_spent, qt_impressions, qt_outbound_clicks
  FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
),

midia AS (
  SELECT
    w.sigla,
    SUM(IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.vl, 0))          AS vl_tag,
    SUM(s.vl)                                                             AS vl_janela,
    SUM(IF(s.nm_fonte = 'meta' AND REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.vl, 0)) AS vl_tag_meta,
    SUM(IF(s.nm_fonte = 'meta', s.vl, 0))                                 AS vl_janela_meta,
    SUM(IF(s.nm_fonte <> 'meta', s.vl, 0))                                AS vl_janela_google,
    COUNT(DISTINCT IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx) AND s.vl > 0,
                      s.id_campanha, NULL))                               AS qt_campanhas_midia_tag,
    SUM(IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.qt_impressoes, 0)) AS qt_impressoes_tag,
    SUM(IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.qt_cliques, 0))    AS qt_cliques_tag
  FROM win AS w
  LEFT JOIN spend AS s ON s.dt BETWEEN w.dt_ini AND w.dt_fim
  GROUP BY 1
),

comp AS (
  SELECT
    sigla,
    COUNT(*)                                              AS qt_compradores,
    COUNTIF(st_status_compra = 'nao_membro')              AS qt_nao_membros,
    COUNTIF(nm_canal = 'midia_paga')                      AS qt_compradores_midia,
    SUM(vl_receita)                                       AS vl_receita,
    SUM(IF(nm_canal = 'midia_paga', vl_receita, 0))       AS vl_receita_midia
  FROM `bp-staging.dbt_abe.tb_ht_compradores`
  WHERE bl_universo_principal
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  c.qt_compradores,
  ROUND(c.vl_receita)      AS vl_receita,
  ROUND(m.vl_tag)          AS vl_midia_tag,
  ROUND(m.vl_janela)       AS vl_midia_janela,
  m.qt_campanhas_midia_tag,
  -- CAC nas duas leituras
  ROUND(m.vl_tag    / NULLIF(c.qt_compradores, 0), 2) AS vl_cac_tag,
  ROUND(m.vl_janela / NULLIF(c.qt_compradores, 0), 2) AS vl_cac_janela,
  -- CAC de aquisição pura (só não-membros no denominador)
  ROUND(m.vl_tag    / NULLIF(c.qt_nao_membros, 0), 2) AS vl_cac_nao_membro,
  -- CAC do canal mídia: verba da tag ÷ compradores que chegaram por mídia
  ROUND(m.vl_tag    / NULLIF(c.qt_compradores_midia, 0), 2) AS vl_cac_canal_midia,
  -- ROAS
  ROUND(c.vl_receita       / NULLIF(m.vl_tag, 0), 2)    AS vl_roas_tag,
  ROUND(c.vl_receita_midia / NULLIF(m.vl_tag, 0), 2)    AS vl_roas_midia_direta,
  -- preço do canal (o CAC sobe por preço de mídia ou por conversão?)
  ROUND(1000 * m.vl_tag / NULLIF(m.qt_impressoes_tag, 0), 2) AS vl_cpm_tag,
  ROUND(m.vl_tag / NULLIF(m.qt_cliques_tag, 0), 2)           AS vl_cpc_tag,
  ROUND(100 * c.qt_compradores_midia / NULLIF(m.qt_cliques_tag, 0), 3) AS pct_conv_clique_compra
FROM win AS w
LEFT JOIN midia AS m USING (sigla)
LEFT JOIN comp  AS c USING (sigla)
ORDER BY w.ord;
