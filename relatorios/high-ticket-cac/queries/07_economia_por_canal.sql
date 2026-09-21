-- High-ticket: economia de cada canal, campanha a campanha.
--
-- Responde "CAC por canal": para cada campanha × canal, quanto custou, quantos compradores
-- trouxe e quanto rendeu. Os canais têm naturezas de custo diferentes e isso é explícito aqui:
--
--   midia_paga  -> verba de anúncio com a sigla no nome (Meta via Marketing API + Google + PMax).
--                  Custo 100% variável e 100% atribuível.
--   comercial   -> COMISSÃO de 9% sobre a receita do canal (premissa do André, set/2026).
--                  ⚠️ É PISO: não inclui folha, ferramenta (Zenvia) nem estrutura. O CAC do
--                  Comercial calculado aqui é o custo marginal da venda, não o custo do canal.
--   crm         -> disparos da Insider COM A TAG da campanha × preço por canal:
--                  WhatsApp R$ 0,323/entrega (fonte canônica: wiki zenvia-custos.md, que corrige
--                  o antigo R$ 0,33); e-mail R$ 0,0008/entrega; push e in-app R$ 0 (inclusos na
--                  plataforma). ⚠️ O e-mail é contratado — na prática é custo fixo, e o
--                  R$ 0,0008 é a diluição por envio, não um custo marginal real.
--   organico    -> sem custo atribuível (não é "de graça": é mídia e conteúdo de outras frentes).
--
-- ⚠️ Assimetria que não dá para eliminar: a verba de mídia é do lançamento inteiro (inclusive o
--    aquecimento que alimentou as vendas dos OUTROS canais), enquanto comissão e disparo são
--    custos incorridos por venda. O CAC de mídia aqui é, portanto, o mais conservador dos três.
-- ⚠️ A Insider só tem dados desde 30/01/2024: a Travessia (2023) sai sem custo de CRM.

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

-- compradores e receita por canal
canal AS (
  SELECT
    sigla,
    nm_canal,
    COUNT(*)                                 AS qt_compradores,
    SUM(vl_receita)                          AS vl_receita,
    COUNTIF(st_status_compra = 'nao_membro') AS qt_nao_membros,
    COUNTIF(NOT bl_ht_previo)                AS qt_primeira_ht
  FROM `bp-staging.dbt_abe.tb_ht_compradores`
  WHERE bl_universo_principal
  GROUP BY 1, 2
),

-- custo de mídia: verba das campanhas de anúncio com a sigla
spend AS (
  SELECT dt, nm_campanha, vl_spend AS vl FROM `bp-staging.dbt_abe.tb_ht_meta_spend`
  UNION ALL
  SELECT reference_date, nm_campaign_name, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
  UNION ALL
  SELECT reference_date, nm_campaign_name, vl_amount_spent FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
),

custo_midia AS (
  SELECT w.sigla, SUM(s.vl) AS vl_custo
  FROM win AS w
  JOIN spend AS s
    ON s.dt BETWEEN w.dt_ini AND w.dt_fim
   AND REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx)
  GROUP BY 1
),

-- custo de CRM: disparos com a tag da campanha, precificados por canal
custo_crm AS (
  SELECT
    w.sigla,
    SUM(i.qt_insider_delivered) AS qt_disparos,
    SUM(CASE i.nm_channel
          WHEN 'whatsapp' THEN i.qt_insider_delivered * 0.323
          WHEN 'email'    THEN i.qt_insider_delivered * 0.0008
          ELSE 0
        END) AS vl_custo,
    SUM(IF(i.nm_channel = 'email',    i.qt_insider_delivered, 0)) AS qt_email,
    SUM(IF(i.nm_channel = 'whatsapp', i.qt_insider_delivered, 0)) AS qt_whatsapp,
    SUM(IF(i.nm_channel = 'app_push', i.qt_insider_delivered, 0)) AS qt_push,
    SUM(IF(i.nm_channel NOT IN ('email','whatsapp','app_push'), i.qt_insider_delivered, 0)) AS qt_outros,
    SUM(i.qt_insider_click) AS qt_cliques
  FROM win AS w
  JOIN `bp-datawarehouse.datamart.dtm_analytics_revenue_insider_funnel` AS i
    ON i.dt_dispatch_date BETWEEN w.dt_ini AND w.dt_fim
   AND UPPER(i.nm_campaign_tag) = w.tag
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  c.nm_canal,
  c.qt_compradores,
  ROUND(c.vl_receita)                                  AS vl_receita,
  c.qt_nao_membros,
  c.qt_primeira_ht,
  -- custo do canal, cada um com a sua natureza
  ROUND(CASE c.nm_canal
          WHEN 'midia_paga' THEN cm.vl_custo
          WHEN 'comercial'  THEN c.vl_receita * 0.09
          WHEN 'crm'        THEN cc.vl_custo
          ELSE 0
        END, 2)                                        AS vl_custo,
  CASE c.nm_canal
    WHEN 'midia_paga' THEN 'verba de anúncio (tag)'
    WHEN 'comercial'  THEN 'comissão 9% (piso — sem folha)'
    WHEN 'crm'        THEN 'disparo com a tag (WA 0,323 / e-mail 0,0008)'
    ELSE 'sem custo atribuível'
  END                                                  AS nm_natureza_custo,
  ROUND(CASE c.nm_canal
          WHEN 'midia_paga' THEN cm.vl_custo
          WHEN 'comercial'  THEN c.vl_receita * 0.09
          WHEN 'crm'        THEN cc.vl_custo
          ELSE NULL
        END / NULLIF(c.qt_compradores, 0), 2)          AS vl_cac_canal,
  ROUND(c.vl_receita / NULLIF(CASE c.nm_canal
          WHEN 'midia_paga' THEN cm.vl_custo
          WHEN 'comercial'  THEN c.vl_receita * 0.09
          WHEN 'crm'        THEN cc.vl_custo
          ELSE NULL
        END, 0), 2)                                    AS vl_roas_canal,
  ROUND(c.vl_receita / NULLIF(c.qt_compradores, 0))     AS vl_ticket,
  -- só faz sentido no canal CRM
  IF(c.nm_canal = 'crm', cc.qt_disparos,  NULL)         AS qt_disparos,
  IF(c.nm_canal = 'crm', cc.qt_email,     NULL)         AS qt_email,
  IF(c.nm_canal = 'crm', cc.qt_whatsapp,  NULL)         AS qt_whatsapp,
  IF(c.nm_canal = 'crm', cc.qt_push,      NULL)         AS qt_push,
  IF(c.nm_canal = 'crm', cc.qt_outros,    NULL)         AS qt_outros,
  IF(c.nm_canal = 'crm', ROUND(c.vl_receita / NULLIF(cc.qt_disparos / 1000, 0), 2), NULL) AS vl_receita_por_1k,
  -- ⚠️ Mesma métrica excluindo push do denominador. O push não tem telemetria (o relatório já
  -- diz para tratá-lo como alcance) e saiu de 0% do volume no BNO24 para 35% no BP10 — mantê-lo
  -- no denominador exagera a deterioração. Levantado na revisão de 17/09.
  IF(c.nm_canal = 'crm',
     ROUND(c.vl_receita / NULLIF((cc.qt_email + cc.qt_whatsapp) / 1000, 0), 2), NULL) AS vl_receita_por_1k_sem_push
FROM win AS w
JOIN canal       AS c  USING (sigla)
LEFT JOIN custo_midia AS cm USING (sigla)
LEFT JOIN custo_crm   AS cc USING (sigla)
WHERE c.nm_canal IN ('midia_paga', 'comercial', 'crm', 'organico_portal')
ORDER BY w.ord, c.vl_receita DESC;
