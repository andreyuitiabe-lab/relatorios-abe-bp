-- High-ticket: esforço de CRM e de Comercial por campanha.
--
-- Responde "a gente fez alguma coisa diferente?" pelo lado do trabalho gasto:
--   CRM       — disparos entregues por canal (email/WhatsApp/push/in-app) e receita atribuída
--   Comercial — abordagens Zenvia, conversas reais (com resposta do cliente) e conversão
--
-- Duas leituras de CRM, porque a tag não cobre tudo:
--   por_tag  — peças com a sigla da campanha em nm_campaign_tag
--   janela   — TODO o disparo do período (é a leitura certa para Black November, que é
--              promoção do catálogo inteiro; e é o denominador de "intensidade de CRM")
--
-- ⚠️ COBERTURA: dtm_analytics_revenue_insider_funnel começa em 30/01/2024 — a Travessia
--    (abr-mai/2023) NÃO tem CRM medível. Zenvia começa em 28/09/2022 e cobre tudo.
-- ⚠️ Taxa de abertura de email tem quebra de série em 23/03/2026 (passou a contar só
--    abertura humana) — não comparar abertura pré vs pós. Entrega e clique são comparáveis.
-- ⚠️ app_push não tem telemetria de abertura/clique (140M+ entregues, ~19 opens).

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, 'TRA'   AS tag, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', 'TRA',   2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', 'BNO24', 3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', 'BIT',   4 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', 'DBI',   6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', 'CDL',   7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', 'BP10',  8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', 'ODI',   9
),

crm AS (
  SELECT
    w.sigla,
    SUM(IF(UPPER(i.nm_campaign_tag) = w.tag, i.qt_insider_delivered, 0))        AS qt_entregue_tag,
    SUM(i.qt_insider_delivered)                                                 AS qt_entregue_janela,
    SUM(IF(i.nm_channel = 'email',    i.qt_insider_delivered, 0))               AS qt_email,
    SUM(IF(i.nm_channel = 'whatsapp', i.qt_insider_delivered, 0))               AS qt_whatsapp,
    SUM(IF(i.nm_channel = 'app_push', i.qt_insider_delivered, 0))               AS qt_push,
    SUM(IF(UPPER(i.nm_campaign_tag) = w.tag, i.vl_total_revenue, 0))            AS vl_receita_crm_tag,
    SUM(i.vl_total_revenue)                                                     AS vl_receita_crm_janela,
    SUM(IF(i.nm_channel = 'whatsapp', i.qt_insider_delivered, 0)) * 0.40        AS vl_custo_whatsapp_est,
    SUM(IF(i.nm_channel = 'email',    i.qt_insider_delivered, 0)) * 0.0008      AS vl_custo_email_est
  FROM win AS w
  JOIN `bp-datawarehouse.datamart.dtm_analytics_revenue_insider_funnel` AS i
    ON i.dt_dispatch_date BETWEEN w.dt_ini AND w.dt_fim
  GROUP BY 1
),

-- abordagens do Comercial na janela (grupo Comercial, padrão do relatório comercial-abordagens)
abordagens AS (
  SELECT
    w.sigla,
    COUNT(*)                                        AS qt_abordagens,
    COUNTIF(a.qt_prospect_interactions > 0)         AS qt_conversas_reais,
    COUNT(DISTINCT a.id_prospect)                   AS qt_pessoas_abordadas
  FROM win AS w
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_approaches` AS a
    ON DATE(a.dt_approach_start) BETWEEN w.dt_ini AND w.dt_fim
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_contacts` AS z USING (id_prospect)
  WHERE TRIM(z.nm_group) = 'Comercial'
  GROUP BY 1
),

-- vendas do Comercial na janela (todas, não só as da campanha) — mede a produção do canal
vendas_comercial AS (
  SELECT
    w.sigla,
    COUNT(*)                          AS qt_vendas_comercial,
    SUM(t.vl_payment_gross)           AS vl_receita_comercial,
    COUNT(DISTINCT t.id_gateway_customer) AS qt_clientes_comercial
  FROM win AS w
  JOIN `bp-datawarehouse.masterdata.fct_transactions` AS t
    ON DATE(t.dt_ordered_at) BETWEEN w.dt_ini AND w.dt_fim
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.bl_is_commercial_channel = TRUE
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1 AS qt_dias,
  -- CRM
  c.qt_entregue_tag,
  c.qt_entregue_janela,
  ROUND(c.qt_entregue_janela / (DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1)) AS qt_disparos_dia,
  ROUND(100 * c.qt_whatsapp / NULLIF(c.qt_entregue_janela, 0), 2) AS pct_whatsapp,
  ROUND(c.vl_receita_crm_tag)    AS vl_receita_crm_tag,
  ROUND(c.vl_receita_crm_janela) AS vl_receita_crm_janela,
  ROUND(c.vl_receita_crm_janela / NULLIF(c.qt_entregue_janela / 1000, 0), 2) AS vl_receita_por_1k,
  ROUND(c.vl_receita_crm_janela / NULLIF(c.vl_custo_whatsapp_est + c.vl_custo_email_est, 0), 2) AS vl_roi_crm_est,
  -- Comercial
  a.qt_abordagens,
  a.qt_conversas_reais,
  ROUND(100 * a.qt_conversas_reais / NULLIF(a.qt_abordagens, 0), 2) AS pct_resposta,
  ROUND(a.qt_abordagens / (DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1)) AS qt_abordagens_dia,
  v.qt_vendas_comercial,
  ROUND(v.vl_receita_comercial) AS vl_receita_comercial,
  ROUND(100 * v.qt_clientes_comercial / NULLIF(a.qt_pessoas_abordadas, 0), 2) AS pct_conv_abordagem,
  ROUND(v.vl_receita_comercial / NULLIF(a.qt_conversas_reais, 0), 2) AS vl_receita_por_conversa
FROM win AS w
LEFT JOIN crm AS c USING (sigla)
LEFT JOIN abordagens AS a USING (sigla)
LEFT JOIN vendas_comercial AS v USING (sigla)
ORDER BY w.ord;
