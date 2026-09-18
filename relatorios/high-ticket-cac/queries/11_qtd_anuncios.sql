-- High-ticket: quantos anúncios cada campanha rodou (item "Qtd. ads" do pedido original).
--
-- ⚠️ COBERTURA PARCIAL, e a razão importa:
--   • Contagem de ANÚNCIOS (`nm_ad_name`) só existe no warehouse, que tem Meta desde ago/2025 →
--     cobre BNO25, DBI, CDL, BP10 e ODI (5 das 9).
--   • Para TRA, TRA2, BNO24 e BIT a contagem de anúncios exigiria a Marketing API em `level=ad`.
--     A extração foi montada (`scripts/extrai_meta_ads.py`) mas **o token da Meta foi invalidado
--     em 18/09/2026** (erro 190/subcode 460 — sessão encerrada por troca de senha ou decisão do
--     Facebook). Assim que o token for renovado, rodar o script fecha as 4 que faltam.
--   • Contagem de CAMPANHAS de anúncio existe para as 9, da extração de nível de campanha que já
--     está em `tb_ht_meta_spend` — é o piso disponível hoje.
--
-- Google e PMax ficam de fora da contagem de anúncios: o PMax não tem nível de anúncio (a
-- granularidade máxima é campanha) e o Google Ads do warehouse traz `id_advertising`, não nome
-- comparável. Contar os três juntos misturaria unidades.

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

-- anúncios: só o mart do Meta tem nome de anúncio (desde ago/2025)
anuncios AS (
  SELECT
    w.sigla,
    COUNT(DISTINCT f.nm_ad_name)     AS qt_anuncios,
    COUNT(DISTINCT f.nm_ad_set_name) AS qt_conjuntos,
    SUM(f.vl_amount_spent)           AS vl_spend_meta
  FROM win AS w
  JOIN `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel` AS f
    ON f.reference_date BETWEEN w.dt_ini AND w.dt_fim
   AND REGEXP_CONTAINS(UPPER(f.nm_campaign_name), w.rx)
  WHERE f.vl_amount_spent > 0
  GROUP BY 1
),

-- campanhas de anúncio: existe para as 9 (Marketing API, nível de campanha)
campanhas_midia AS (
  SELECT
    w.sigla,
    COUNT(DISTINCT m.id_campanha) AS qt_campanhas_meta,
    SUM(m.vl_spend)               AS vl_spend_api
  FROM win AS w
  JOIN `bp-staging.dbt_abe.tb_ht_meta_spend` AS m
    ON m.dt BETWEEN w.dt_ini AND w.dt_fim
   AND REGEXP_CONTAINS(UPPER(m.nm_campanha), w.rx)
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  a.qt_anuncios,
  a.qt_conjuntos,
  c.qt_campanhas_meta,
  ROUND(a.vl_spend_meta / NULLIF(a.qt_anuncios, 0))   AS vl_spend_por_anuncio,
  CASE
    WHEN a.qt_anuncios IS NOT NULL THEN 'warehouse (Meta, ago/2025+)'
    ELSE 'sem contagem de anúncio — token Meta invalidado em 18/09'
  END AS nm_fonte_contagem
FROM win AS w
LEFT JOIN anuncios        AS a USING (sigla)
LEFT JOIN campanhas_midia AS c USING (sigla)
ORDER BY w.ord;
