-- High-ticket: quantas PEÇAS cada campanha colocou no ar — anúncios e e-mails distintos.
--
-- Mede produção criativa, não entrega: um e-mail disparado para 3 milhões de pessoas conta 1.
-- É o par natural da "qtd. de ads" do pedido original.
--
-- Anúncios  -> `nm_ad_name` distinto em dtm_analytics_facebook_ads_funnel (Meta).
--              ⚠️ warehouse só tem Meta desde ago/2025 → cobre BNO25, DBI, CDL, BP10, ODI.
--              Conta as duas versões: com verba (rodou de fato) e todas as linhas (inclui
--              anúncio que existiu no conjunto e não recebeu entrega).
-- E-mails   -> `nm_campaign` distinto em dtm_analytics_revenue_insider_funnel com
--              nm_channel='email'. O nome é a própria peça (`EM01 - [BNO24] [ENG] ...`).
--              ⚠️ Insider começa em 30/01/2024 → a Travessia (2023) fica sem contagem.
--
-- Duas leituras por campanha, porque respondem coisas diferentes:
--   _tag    — peças que carregam a sigla da campanha (produção dedicada ao lançamento)
--   _janela — tudo que foi ao ar no período (carga total de comunicação que a base recebeu,
--             incluindo always-on de outras frentes). É o denominador de "fadiga de canal".

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, 'TRA'   AS tag, r'\[TRA\]|TRAVESSIA'   AS rx, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', 'TRA',   r'\[TRA\]|TRAVESSIA',                               2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', 'BNO24', r'\[BNO24\]|\[BNO\]|BLACK',                         3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', 'BIT',   r'\[BIT\]|NOVA MOEDA|BITCOIN',                      4 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', 'DBI',   r'\[DBI\]|BITCOIN',                                 6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', 'CDL',   r'\[CDL\]|CLUBE DO LIVRO',                          7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', 'BP10',  r'\[BP10\]|10 ANOS|ANIVERS',                        8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', 'ODI',   r'\[ODI\]|ODISSEIA',                                9
),

ads AS (
  SELECT
    w.sigla,
    COUNT(DISTINCT IF(f.vl_amount_spent > 0, f.nm_ad_name, NULL)) AS qt_anuncios_com_verba,
    COUNT(DISTINCT f.nm_ad_name)                                  AS qt_anuncios_total,
    COUNT(DISTINCT f.nm_ad_set_name)                              AS qt_conjuntos
  FROM win AS w
  JOIN `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel` AS f
    ON f.reference_date BETWEEN w.dt_ini AND w.dt_fim
   AND REGEXP_CONTAINS(UPPER(f.nm_campaign_name), w.rx)
  GROUP BY 1
),

crm AS (
  -- ⚠️ CORREÇÃO 21/09/2026 (o André desconfiou do volume e estava certo): `nm_campaign` distinto
  --    NÃO é peça criativa. O CRM manda o mesmo e-mail em várias versões por bloco da base, com
  --    o marcador [B00]..[B11] no nome — o EM03 do BNO24 saiu em 12 versões. Contar nome distinto
  --    dava 581 e-mails no BNO24 quando a régua vai só até EM55.
  --
  --    Três medidas diferentes, e o relatório mostra as três:
  --      qt_disparos_distintos — nomes distintos (o que a contagem antiga media)
  --      qt_pecas              — identidade da peça: prefixo numerado, ou o nome sem o [Bnn].
  --                              ⚠️ HEURÍSTICA: onde não há prefixo nem marcador de bloco, duas
  --                              variantes viram duas peças. Superestima o BNO24, que tem 135
  --                              nomes de WhatsApp sem prefixo. Usar como ordem de grandeza.
  --      qt_entregas_por_disparo — ENTREGAS ÷ disparos distintos. Não depende de heurística
  --                              nenhuma e é a medida robusta de "quão segmentado foi": quanto
  --                              maior, mais gente recebeu a mesma mensagem.
  SELECT
    w.sigla,
    COUNT(DISTINCT IF(i.nm_channel='email',    i.nm_campaign, NULL))    AS qt_email_tag,
    COUNT(DISTINCT IF(i.nm_channel='whatsapp', i.nm_campaign, NULL))    AS qt_whatsapp_tag,
    COUNT(DISTINCT IF(i.nm_channel='app_push', i.nm_campaign, NULL))    AS qt_push_tag,
    COUNT(DISTINCT i.nm_campaign)                                       AS qt_disparos_distintos,
    COUNT(DISTINCT COALESCE(
      REGEXP_EXTRACT(i.nm_campaign, r'^([A-Za-z]{2,4}\s?[0-9]+)'),
      TRIM(REGEXP_REPLACE(i.nm_campaign, r'\[B[0-9]{1,2}\]', ''))))   AS qt_pecas,
    SUM(i.qt_insider_delivered)                                         AS qt_entregas_tag,
    COUNT(DISTINCT IF(i.nm_channel='email', i.nm_campaign, NULL))       AS qt_email_janela_dummy
  FROM win AS w
  JOIN `bp-datawarehouse.datamart.dtm_analytics_revenue_insider_funnel` AS i
    ON i.dt_dispatch_date BETWEEN w.dt_ini AND w.dt_fim
   AND UPPER(i.nm_campaign_tag) = w.tag
   AND i.nm_channel IN ('email','whatsapp','app_push')
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1                              AS qt_dias,
  -- anúncios
  a.qt_anuncios_com_verba,
  a.qt_anuncios_total,
  a.qt_conjuntos,
  -- e-mails e demais peças de CRM
  c.qt_email_tag,
  c.qt_whatsapp_tag,
  c.qt_push_tag,
  c.qt_disparos_distintos                                             AS qt_pecas_crm_tag,
  c.qt_pecas,
  ROUND(c.qt_disparos_distintos / NULLIF(c.qt_pecas, 0), 1)           AS qt_variantes_por_peca,
  ROUND(c.qt_pecas / (DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1), 2)     AS qt_pecas_por_dia_real,
  -- ritmo de produção
  ROUND(c.qt_disparos_distintos
        / (DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1), 2)                AS qt_pecas_crm_por_dia,
  ROUND(a.qt_anuncios_com_verba / (DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1), 2) AS qt_anuncios_por_dia,
  -- quantas entregas cada peça de CRM carregou, em média
  ROUND(c.qt_entregas_tag / NULLIF(c.qt_disparos_distintos, 0))       AS qt_entregas_por_disparo
FROM win AS w
LEFT JOIN ads AS a USING (sigla)
LEFT JOIN crm AS c USING (sigla)
ORDER BY w.ord;
