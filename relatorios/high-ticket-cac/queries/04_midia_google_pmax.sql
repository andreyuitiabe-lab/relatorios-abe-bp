-- High-ticket: spend Google Ads + PMax por campanha (warehouse).
--
-- ⚠️ COBERTURA: os marts de Google e PMax só têm spend desde jan/2025 (verificado 17/09/2026:
--    série mensal vazia antes disso). Para TRA (2023), TRA2 (2024) e BNO24 (nov/2024) a única
--    fonte de Google é a planilha do time de tráfego, que não separa canal — está marcado como
--    NULL aqui e tratado no memo.
-- ⚠️ O spend Meta NÃO vem daqui: o mart de Meta só começa em ago/2025. Meta vem da Marketing
--    API (scripts/extrai_meta_api.py), que alcança 37 meses (desde 17/08/2023).
--
-- Duas medidas por campanha:
--   spend_tag     — campanhas de mídia com a sigla no nome (atribuível ao lançamento)
--   spend_janela  — todo o spend da fonte no período (denominador do CAC blended)

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, r'\[TRA\]|TRAVESSIA'          AS rx, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', r'\[TRA\]|TRAVESSIA',                               2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', r'\[BNO24\]|\[BNO\]|BLACK',                         3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', r'\[BIT\]|NOVA MOEDA|BITCOIN',                      4 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', r'\[DBI\]|BITCOIN',                                 6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', r'\[CDL\]|CLUBE DO LIVRO',                          7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', r'\[BP10\]|10 ANOS|ANIVERS',                        8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', r'\[ODI\]|ODISSEIA',                                9
),

spend AS (
  SELECT 'google' AS nm_fonte, reference_date AS dt, nm_campaign_name AS nm_campanha, vl_amount_spent AS vl
  FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
  UNION ALL
  SELECT 'pmax', reference_date, nm_campaign_name, vl_amount_spent
  FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
)

SELECT
  w.ord,
  w.sigla,
  ROUND(SUM(IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.vl, 0)))            AS vl_spend_tag,
  ROUND(SUM(s.vl))                                                               AS vl_spend_janela,
  COUNT(DISTINCT IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.nm_campanha, NULL)) AS qt_campanhas_tag,
  ROUND(SUM(IF(s.nm_fonte = 'google', s.vl, 0)))                                 AS vl_google,
  ROUND(SUM(IF(s.nm_fonte = 'pmax',   s.vl, 0)))                                 AS vl_pmax
FROM win AS w
LEFT JOIN spend AS s
  ON s.dt BETWEEN w.dt_ini AND w.dt_fim
GROUP BY 1, 2
ORDER BY w.ord;
