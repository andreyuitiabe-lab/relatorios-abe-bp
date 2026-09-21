-- High-ticket: CAC e saturação — universo de compradores por campanha
-- Materializa bp-staging.dbt_abe.tb_ht_compradores: 1 linha por comprador × campanha.
--
-- TRÊS UNIVERSOS, calculados para TODAS as campanhas (a coluna bl_universo_principal
-- marca qual vale para cada uma; os outros ficam como sensibilidade — a margem de erro
-- de uma campanha é a regra, não o dado):
--   'rastro'  — união de tracking ∪ utm_campaign ∪ utm_content ∪ checkout_name, regex
--               ancorado em fronteira de não-letra (padrão validado em aquecimento-vendas).
--               É o universo PRINCIPAL dos 7 lançamentos de produto, porque captura o
--               upsell vendido dentro da campanha — que é onde o high-ticket monetiza:
--               BIT sem isso perde 70% da receita (Black), CDL perde os R$ 2,8 mi de
--               Black Vitalício do cashback, TRA perde R$ 1,57 mi de Mecenas Travessia.
--               Reproduz as referências conhecidas: BIT 1.549 compradores / R$ 2,61 mi
--               (aquecimento-vendas: 1.540 / R$ 2,6 mi) e DBI R$ 0,22 mi (wiki: R$ 244k).
--   'janela'  — toda venda nova do período. É o universo PRINCIPAL dos dois Black November,
--               que são promoção do catálogo inteiro (rastro ali não significa nada).
--               Validado contra a planilha do time de tráfego: BNO24 R$ 40,33 mi (planilha)
--               vs R$ 40,28 mi (warehouse); BNO25 R$ 18,83 mi vs R$ 18,72 mi.
--   'produto' — só o plano do lançamento. Serve de piso e de leitura "produto puro".
-- ⚠️ BP10: regex ancorado em bp10/aniversário/10-anos. NÃO usar 'contains 10' (regra do
--    dashboard de campanhas): casa o tier [10r] (Apoiador R$ 10) e infla ~8k vendas —
--    ver metricas-referencia.md §BP10.
--
-- STATUS DO COMPRADOR (as 3 categorias pedidas: membro / ex-membro / não-membro),
-- avaliado na data da PRIMEIRA compra da campanha, com buffer de 1h em dt_started_at
-- para não classificar como membro a assinatura criada pela própria compra.
-- ⚠️ Usa WHITELIST de membership: `dim_subscriptions` registra produto avulso como
-- assinatura ativa (clube-do-livro, livro-odisseia*, travessia, certificações...), e
-- sem a whitelist todo comprador de livro viraria "membro" — erro enorme justamente
-- nas campanhas CDL/ODI desta análise. Ver bq-regras.md §Gotchas Teller.
-- Legados incluídos como membership: patriota (304k subs, tier principal até 2022),
-- bp-select, fraterno, combo-liberdade. Excluídos os clubes de conteúdo de 2021
-- (sociedade-do-livro, clube-da-musica, escola-da-familia) — são add-on, não acesso.
--
-- Filtros padrão: nm_status='approved', bl_is_renovation=FALSE (regras-negocio.md).

CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_ht_compradores` AS

WITH win AS (
  SELECT 'TRA'   AS sigla, 'Travessia'              AS nm_campanha, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, 'rastro' AS nm_regra_principal, r'travessia' AS rx, 1 AS ord UNION ALL
  SELECT 'TRA2',          'Travessia 2ª turma',     DATE '2024-04-01', DATE '2024-05-31', 'rastro', r'travessia', 2 UNION ALL
  SELECT 'BNO24',         'Black November 2024',    DATE '2024-11-01', DATE '2024-11-30', 'janela',  r'bno24|black[ _-]?(friday|november)|(^|[^a-z])bf24([^a-z]|$)', 3 UNION ALL
  SELECT 'BIT',           'Certificação Bitcoin 1', DATE '2025-04-09', DATE '2025-05-31', 'rastro',  r'(^|[^a-z])bit([^a-z]|$)|nova[ _-]moeda|bitcoin', 4 UNION ALL
  -- ⚠️ O BNO25 saiu do ESCOPO DO RELATÓRIO em 21/09/2026 (decisão do André, a pedido da Bárbara:
  --    "foi foco em entrada mesmo"). Ele continua NESTA tabela de propósito: é o histórico de
  --    compra da base, e o DBI tem o BNO25 como origem principal de reincidência. Tirá-lo daqui
  --    faria a reincidência do DBI cair por artefato de escopo, não por fato.
  --    Todas as demais queries já não o listam — ele não aparece em nenhuma saída do relatório.
  SELECT 'BNO25',         'Black November 2025',    DATE '2025-11-01', DATE '2025-11-30', 'janela',  r'bno25|black[ _-]?(friday|november)|(^|[^a-z])bf25([^a-z]|$)', 5 UNION ALL
  SELECT 'DBI',           'Certificação Bitcoin 2', DATE '2026-02-04', DATE '2026-03-31', 'rastro',  r'(^|[^a-z])dbi([^a-z]|$)|bitcoin|nova[ _-]moeda', 6 UNION ALL
  SELECT 'CDL',           'Clube do Livro',         DATE '2026-05-05', DATE '2026-06-30', 'rastro', r'(^|[^a-z])cdl([^a-z]|$)|clube[ _-]do[ _-]livro', 7 UNION ALL
  SELECT 'BP10',          'BP 10 Anos',             DATE '2026-06-11', DATE '2026-09-15', 'rastro',  r'bp[ _-]?10|10[ _-]anos|dez[ _-]anos|anivers', 8 UNION ALL
  SELECT 'ODI',           'Odisseia Colecionador',  DATE '2026-07-17', DATE '2026-09-16', 'rastro', r'(^|[^a-z])odi([^a-z]|$)|odisseia', 9
),

-- cada campanha é medida nos DOIS universos; a coluna nm_regra_principal marca qual vale
universo AS (
  SELECT 'produto' AS nm_universo UNION ALL SELECT 'rastro' UNION ALL SELECT 'janela'
),

-- regra 'produto': planos que definem cada lançamento
plano_campanha AS (
  SELECT 'TRA'  AS sigla, p FROM UNNEST(['travessia', 'travessia-familia']) p UNION ALL
  SELECT 'TRA2',       p FROM UNNEST(['travessia', 'travessia-familia']) p UNION ALL
  SELECT 'BIT',        p FROM UNNEST(['bitcoin', 'funil-bitcoin', 'desafio-bitcoin']) p UNION ALL
  SELECT 'DBI',        p FROM UNNEST(['bitcoin', 'bitcoin-20', 'funil-bitcoin', 'desafio-bitcoin']) p UNION ALL
  SELECT 'CDL',        p FROM UNNEST(['clube-do-livro', 'clube-do-livro-basico']) p UNION ALL
  SELECT 'ODI',        p FROM UNNEST(['livro-odisseia-edicao-colecionador', 'livro-odisseia',
                                      'odisseia-curso-avulso', 'odisseia-ebook-curso']) p
),

tx AS (
  SELECT
    w.sigla,
    u.nm_universo,
    t.id_gateway_customer,
    t.dt_ordered_at,
    t.vl_payment_gross,
    t.bl_is_commercial_channel,
    t.nm_gateway_plan,
    t.nm_plan_label,
    LOWER(t.nm_pptc_tracking_name) AS trk,
    LOWER(t.nm_pptc_utm_medium)    AS utm_medium
  FROM `bp-datawarehouse.masterdata.fct_transactions` AS t
  JOIN win AS w
    ON DATE(t.dt_ordered_at) BETWEEN w.dt_ini AND w.dt_fim
  CROSS JOIN universo AS u
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND (
      -- 'janela': promoção do catálogo inteiro, entra toda venda nova do período
      u.nm_universo = 'janela'
      -- 'produto': só o produto do lançamento
      OR (u.nm_universo = 'produto'
          AND t.nm_gateway_plan IN (SELECT p FROM plano_campanha WHERE sigla = w.sigla))
      -- 'rastro': união de tracking ∪ utm_campaign ∪ utm_content ∪ checkout (padrão aquecimento-vendas)
      OR (u.nm_universo = 'rastro'
          AND REGEXP_CONTAINS(
                LOWER(CONCAT(COALESCE(t.nm_pptc_tracking_name, ''), ' | ',
                             COALESCE(t.nm_pptc_utm_campaign, ''), ' | ',
                             COALESCE(t.nm_pptc_utm_content, ''),  ' | ',
                             COALESCE(t.nm_pptc_checkout_name, ''))),
                w.rx))
    )
),

tx_email AS (
  SELECT tx.*, LOWER(TRIM(c.nm_email)) AS nm_email
  FROM tx
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` AS c USING (id_gateway_customer)
),

compradores AS (
  SELECT
    sigla,
    nm_universo,
    COALESCE(nm_email, CONCAT('__noemail__', id_gateway_customer)) AS id_comprador,
    MIN(dt_ordered_at) AS dt_primeira_compra,
    SUM(vl_payment_gross) AS vl_receita,
    MAX(vl_payment_gross) AS vl_maior_tx,
    COUNT(*) AS qt_tx,
    ARRAY_AGG(STRUCT(bl_is_commercial_channel AS bl_com, trk, utm_medium, nm_plan_label)
              ORDER BY vl_payment_gross DESC LIMIT 1)[OFFSET(0)] AS ptx
  FROM tx_email
  GROUP BY 1, 2, 3
),

-- histórico de assinaturas COM whitelist de membership (exclui produto avulso)
subs AS (
  SELECT
    LOWER(TRIM(u.nm_email)) AS nm_email,
    s.dt_started_at,
    s.dt_expires_in,
    s.nm_subscription_recurrence
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` AS s
  JOIN `bp-datawarehouse.masterdata.dim_user` AS u ON s.id_user = u.id_user
  WHERE s.nm_type = 'paid'
    AND u.nm_email IS NOT NULL
    AND (
      REGEXP_CONTAINS(LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)),
        r'^(bp-)?(good|better|best|black|supporter|mecenas|intermediario|premium|essencial|economico|basico|apoiador|originais|fraterno|patriota|bp-select|combo-liberdade)')
      OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'combo-religioso%'
      OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'combo-essencial%'
      OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'extensao-assinatura-%'
      OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'bolsa-mecenas%'
    )
    AND LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) <> 'essencial-estudar-bem'
),

flag_sub AS (
  SELECT
    c.sigla,
    c.nm_universo,
    c.id_comprador,
    LOGICAL_OR(s.nm_subscription_recurrence = 'vitalício'
               AND s.dt_started_at < DATETIME_SUB(c.dt_primeira_compra, INTERVAL 1 HOUR)) AS bl_vitalicio,
    LOGICAL_OR(s.dt_started_at < DATETIME_SUB(c.dt_primeira_compra, INTERVAL 1 HOUR)
               AND c.dt_primeira_compra BETWEEN s.dt_started_at AND s.dt_expires_in) AS bl_ativo,
    LOGICAL_OR(s.dt_started_at < DATETIME_SUB(c.dt_primeira_compra, INTERVAL 1 HOUR)) AS bl_qualquer_sub
  FROM compradores AS c
  JOIN subs AS s ON s.nm_email = c.id_comprador
  GROUP BY 1, 2, 3
),

-- já havia comprado high-ticket (> R$ 1.000) antes desta campanha?
ht_previo AS (
  SELECT
    c.sigla,
    c.nm_universo,
    c.id_comprador,
    LOGICAL_OR(t.vl_payment_gross > 1000 AND t.dt_ordered_at < c.dt_primeira_compra) AS bl_ht_previo,
    MAX(IF(t.dt_ordered_at < c.dt_primeira_compra, t.dt_ordered_at, NULL))           AS dt_ultima_compra_previa,
    SUM(IF(t.dt_ordered_at < c.dt_primeira_compra, t.vl_payment_gross, 0))           AS vl_gasto_previo
  FROM compradores AS c
  JOIN `bp-datawarehouse.masterdata.dim_contact` AS dc
    ON LOWER(TRIM(dc.nm_email)) = c.id_comprador
  JOIN `bp-datawarehouse.masterdata.fct_transactions` AS t
    ON t.id_gateway_customer = dc.id_gateway_customer
   AND t.nm_status = 'approved'
  GROUP BY 1, 2, 3
),

-- lead da campanha (tag) antes da compra
leads_hist AS (
  SELECT LOWER(TRIM(nm_email)) AS nm_email, nm_tag, MIN(dt_registered_at_br) AS dt_reg
  FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
  WHERE nm_email IS NOT NULL
  GROUP BY 1, 2
),

flag_lead AS (
  SELECT
    c.sigla,
    c.nm_universo,
    c.id_comprador,
    LOGICAL_OR(l.nm_tag = c.sigla AND l.dt_reg < c.dt_primeira_compra) AS bl_lead_campanha
  FROM compradores AS c
  JOIN leads_hist AS l ON l.nm_email = c.id_comprador
  GROUP BY 1, 2, 3
)

SELECT
  c.sigla,
  w.nm_campanha,
  w.ord,
  c.nm_universo,
  (c.nm_universo = w.nm_regra_principal) AS bl_universo_principal,
  c.id_comprador,
  c.dt_primeira_compra,
  c.vl_receita,
  c.vl_maior_tx,
  c.qt_tx,
  c.ptx.nm_plan_label AS nm_plano_principal,
  -- status: as 3 categorias do pedido
  CASE
    WHEN COALESCE(fs.bl_vitalicio, FALSE) OR COALESCE(fs.bl_ativo, FALSE) THEN 'membro'
    WHEN COALESCE(fs.bl_qualquer_sub, FALSE)                              THEN 'ex_membro'
    ELSE 'nao_membro'
  END AS st_status_compra,
  COALESCE(fs.bl_vitalicio, FALSE)  AS bl_vitalicio_previo,
  COALESCE(fl.bl_lead_campanha, FALSE) AS bl_lead_campanha,
  COALESCE(hp.bl_ht_previo, FALSE)  AS bl_ht_previo,
  hp.dt_ultima_compra_previa,
  COALESCE(hp.vl_gasto_previo, 0)   AS vl_gasto_previo,
  -- canal da maior transação da campanha
  CASE
    WHEN c.ptx.bl_com OR STARTS_WITH(COALESCE(c.ptx.trk, ''), 'comercial_') THEN 'comercial'
    WHEN REGEXP_CONTAINS(c.ptx.trk, r'\[fb\+ig\]|\[pmax\]|\[kw\]|\[yt\]|\[publi\]|\[tiktok\]|\[x\]|\[display\]') THEN 'midia_paga'
    WHEN REGEXP_CONTAINS(c.ptx.trk, r'\[e-?mail\]|\[whatsapp\]|\[in-? ?app\]|\[app-? ?push\]|\[web-? ?push\]|\[sms\]|\[custom\]') THEN 'crm'
    WHEN REGEXP_CONTAINS(c.ptx.trk, r'\[canal-yt\]|\[redes sociais\]|\[portal\]|\[programas\]|\[live\]|\[plataforma\]|\[noticias\]|\[assine\]|\[influs\]|\[parceiros\]') THEN 'organico_portal'
    WHEN c.ptx.trk IS NOT NULL THEN 'outros'
    WHEN REGEXP_CONTAINS(c.ptx.utm_medium, r'facebook_ads|meta_ads|pmax|youtube_ads|google_ads|paid_publi|x_ads|^ads$|tiktok') THEN 'midia_paga'
    WHEN REGEXP_CONTAINS(c.ptx.utm_medium, r'whatsapp|email|push|in_app|sms|architect') THEN 'crm'
    WHEN REGEXP_CONTAINS(c.ptx.utm_medium, r'organic|live_youtube|programas|instaportal|home|descricao') THEN 'organico_portal'
    WHEN c.ptx.utm_medium IS NULL THEN 'sem_rastro'
    ELSE 'outros'
  END AS nm_canal
FROM compradores AS c
JOIN win AS w USING (sigla)
LEFT JOIN flag_sub  AS fs ON fs.sigla = c.sigla AND fs.nm_universo = c.nm_universo AND fs.id_comprador = c.id_comprador
LEFT JOIN flag_lead AS fl ON fl.sigla = c.sigla AND fl.nm_universo = c.nm_universo AND fl.id_comprador = c.id_comprador
LEFT JOIN ht_previo AS hp ON hp.sigla = c.sigla AND hp.nm_universo = c.nm_universo AND hp.id_comprador = c.id_comprador;
