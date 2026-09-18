-- High-ticket: quantidade de anúncios por campanha — as DUAS fontes, com definições diferentes.
-- Substitui a 11_qtd_anuncios.sql, que só tinha a fonte do warehouse (5 das 9 campanhas).
--
-- As duas fontes NÃO são intercambiáveis. Reportar as duas, marcando qual é qual:
--
--   A) PLANILHA do time de tráfego (`tb_ht_sheet_meta_ads`)
--      Aba "01. Facebook - Ads - Venda" do arquivo `04.2 Mídia Paga - Anúncios FACEBOOK.xlsx`,
--      carregada por scripts/carrega_planilha_ads.py. 595.265 linhas, 01/06/2022 → 16/04/2026.
--      ⚠️ Só anúncios de fase de VENDA. Campanha com captação pesada sai subcontada — o DBI
--         aparece com 78 anúncios/R$ 19 k aqui contra 284/R$ 152 k no warehouse, porque quase
--         toda a verba dele foi [LEAD].
--      ⚠️ É um XLSX BAIXADO (16/04/2026), não a planilha viva: não atualiza sozinho e não cobre
--         CDL, BP10 nem ODI. Para atualizar, rebaixar o arquivo e rodar o script de carga.
--      Atribuição por regex no nome do ANÚNCIO + nome do CONJUNTO (a aba não traz campanha).
--
--   B) WAREHOUSE (`dtm_analytics_facebook_ads_funnel`)
--      Todas as fases, mas nome de anúncio só é confiável a partir de mar/2025 — antes disso há
--      fragmentos (em nov/2024 são 74 nomes em 56 campanhas, nenhum do BNO24).
--      Atribuição por regex no nome da CAMPANHA.
--
-- Validação cruzada (18/09/2026): no spend mensal as duas fontes batem com a Marketing API em
-- 0,0% em 22 de 31 meses (máx. 3,8%) — é o mesmo dado, recortado diferente.

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, r'\[TRA\]|TRAVESSIA'          AS rx, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', r'\[TRA\]|TRAVESSIA',                               2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', r'\[BNO24\]|\[BNO\]|\[BF\]|BLACK',                  3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', r'\[BIT\]|\[D48\]|NOVA MOEDA|BITCOIN',              4 UNION ALL
  SELECT 'BNO25',         DATE '2025-11-01', DATE '2025-11-30', r'\[BNO25\]|\[BNO\]|BLACK',                         5 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', r'\[DBI\]|BITCOIN',                                 6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', r'\[CDL\]|CLUBE DO LIVRO',                          7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', r'\[BP10\]|10 ANOS|ANIVERS',                        8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', r'\[ODI\]|ODISSEIA',                                9
),

-- A) planilha: anúncios de VENDA
planilha AS (
  SELECT
    w.sigla,
    COUNT(DISTINCT IF(REGEXP_CONTAINS(
      UPPER(CONCAT(p.nm_anuncio, ' ', COALESCE(p.nm_conjunto, ''))), w.rx), p.nm_anuncio, NULL)) AS qt_ads_venda,
    ROUND(SUM(IF(REGEXP_CONTAINS(
      UPPER(CONCAT(p.nm_anuncio, ' ', COALESCE(p.nm_conjunto, ''))), w.rx), p.vl_spend, 0)))     AS vl_spend_venda,
    MAX(p.dt)                                                                                    AS dt_cobertura
  FROM win AS w
  JOIN `bp-staging.dbt_abe.tb_ht_sheet_meta_ads` AS p
    ON p.dt BETWEEN w.dt_ini AND w.dt_fim
  WHERE p.vl_spend > 0
  GROUP BY 1
),

-- B) warehouse: todas as fases
warehouse AS (
  SELECT
    w.sigla,
    COUNT(DISTINCT f.nm_ad_name)     AS qt_ads_todas_fases,
    COUNT(DISTINCT f.nm_ad_set_name) AS qt_conjuntos,
    ROUND(SUM(f.vl_amount_spent))    AS vl_spend_warehouse
  FROM win AS w
  JOIN `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel` AS f
    ON f.reference_date BETWEEN w.dt_ini AND w.dt_fim
   AND REGEXP_CONTAINS(UPPER(f.nm_campaign_name), w.rx)
  WHERE f.vl_amount_spent > 0
    AND f.reference_date >= '2025-03-01'   -- antes disso o nome de anúncio é fragmento, não censo
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  p.qt_ads_venda,
  p.vl_spend_venda,
  b.qt_ads_todas_fases,
  b.qt_conjuntos,
  -- o número a usar, com a origem explícita
  COALESCE(b.qt_ads_todas_fases, p.qt_ads_venda)                          AS qt_anuncios,
  CASE
    WHEN b.qt_ads_todas_fases IS NOT NULL THEN 'warehouse — todas as fases'
    WHEN p.qt_ads_venda       IS NOT NULL THEN 'planilha do tráfego — só fase de venda'
    ELSE 'sem fonte'
  END                                                                     AS nm_fonte_contagem
FROM win AS w
LEFT JOIN planilha  AS p USING (sigla)
LEFT JOIN warehouse AS b USING (sigla)
ORDER BY w.ord;
