-- High-ticket: uma linha por campanha com tudo que o relatório usa.
-- Junta compradores (01), esforço de CRM/Comercial (02), saturação (03) e mídia (05).
--
-- A decomposição central do relatório está aqui:
--   CAC_blended = CAC_do_canal_mídia × share de compradores vindos de mídia
-- Ela é uma identidade aritmética (spend ÷ total = spend ÷ midia × midia ÷ total), e é o
-- que separa "a mídia ficou cara" de "a mídia virou o motor". Ver ANALISE.md.

WITH win AS (
  SELECT 'TRA'   AS sigla, 'Travessia'              AS nm_campanha, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, r'\[TRA\]|TRAVESSIA'          AS rx, 1 AS ord UNION ALL
  SELECT 'TRA2',          'Travessia 2ª turma',     DATE '2024-04-01', DATE '2024-05-31', r'\[TRA\]|TRAVESSIA',                  2 UNION ALL
  SELECT 'BNO24',         'Black November 2024',    DATE '2024-11-01', DATE '2024-11-30', r'\[BNO24\]|\[BNO\]|BLACK',            3 UNION ALL
  SELECT 'BIT',           'Cert. Bitcoin 1',        DATE '2025-04-09', DATE '2025-05-31', r'\[BIT\]|NOVA MOEDA|BITCOIN',         4 UNION ALL
  SELECT 'BNO25',         'Black November 2025',    DATE '2025-11-01', DATE '2025-11-30', r'\[BNO25\]|\[BNO\]|BLACK',            5 UNION ALL
  SELECT 'DBI',           'Cert. Bitcoin 2',        DATE '2026-02-04', DATE '2026-03-31', r'\[DBI\]|BITCOIN',                    6 UNION ALL
  SELECT 'CDL',           'Clube do Livro',         DATE '2026-05-05', DATE '2026-06-30', r'\[CDL\]|CLUBE DO LIVRO',             7 UNION ALL
  SELECT 'BP10',          'BP 10 Anos',             DATE '2026-06-11', DATE '2026-09-15', r'\[BP10\]|10 ANOS|ANIVERS',           8 UNION ALL
  SELECT 'ODI',           'Odisseia',               DATE '2026-07-17', DATE '2026-09-16', r'\[ODI\]|ODISSEIA',                   9
),

comp AS (
  SELECT
    sigla,
    COUNT(*)                                        AS qt_compradores,
    SUM(vl_receita)                                 AS vl_receita,
    AVG(vl_receita)                                 AS vl_ticket,
    COUNTIF(nm_canal = 'midia_paga')                AS qt_comp_midia,
    COUNTIF(nm_canal = 'comercial')                 AS qt_comp_comercial,
    COUNTIF(nm_canal = 'crm')                       AS qt_comp_crm,
    SUM(IF(nm_canal = 'midia_paga',      vl_receita, 0)) AS vl_rec_midia,
    SUM(IF(nm_canal = 'comercial',       vl_receita, 0)) AS vl_rec_comercial,
    SUM(IF(nm_canal = 'crm',             vl_receita, 0)) AS vl_rec_crm,
    SUM(IF(nm_canal = 'organico_portal', vl_receita, 0)) AS vl_rec_organico,
    COUNTIF(st_status_compra = 'membro')            AS qt_membro,
    COUNTIF(st_status_compra = 'ex_membro')         AS qt_ex_membro,
    COUNTIF(st_status_compra = 'nao_membro')        AS qt_nao_membro,
    COUNTIF(NOT bl_ht_previo)                       AS qt_primeira_ht,
    SUM(IF(bl_vitalicio_previo, 0, IF(REGEXP_CONTAINS(LOWER(nm_plano_principal), r'vital'), vl_receita, 0))) AS vl_rec_vitalicio
  FROM `bp-staging.dbt_abe.tb_ht_compradores`
  WHERE bl_universo_principal
  GROUP BY 1
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
    SUM(IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.vl, 0))               AS vl_midia_tag,
    SUM(s.vl)                                                                   AS vl_midia_janela,
    SUM(IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.qt_impressoes, 0))    AS qt_impressoes,
    SUM(IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx), s.qt_cliques, 0))       AS qt_cliques,
    COUNT(DISTINCT IF(REGEXP_CONTAINS(UPPER(s.nm_campanha), w.rx) AND s.vl > 0,
                      s.id_campanha, NULL))                                     AS qt_campanhas_midia
  FROM win AS w
  LEFT JOIN spend AS s ON s.dt BETWEEN w.dt_ini AND w.dt_fim
  GROUP BY 1
),

crm AS (
  SELECT
    w.sigla,
    SUM(i.qt_insider_delivered)  AS qt_disparos,
    SUM(i.vl_total_revenue)      AS vl_receita_crm_janela
  FROM win AS w
  JOIN `bp-datawarehouse.datamart.dtm_analytics_revenue_insider_funnel` AS i
    ON i.dt_dispatch_date BETWEEN w.dt_ini AND w.dt_fim
  GROUP BY 1
),

comercial AS (
  SELECT
    w.sigla,
    COUNT(*)                                AS qt_abordagens,
    COUNTIF(a.qt_prospect_interactions > 0) AS qt_conversas
  FROM win AS w
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_approaches` AS a
    ON DATE(a.dt_approach_start) BETWEEN w.dt_ini AND w.dt_fim
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_contacts` AS z USING (id_prospect)
  WHERE TRIM(z.nm_group) = 'Comercial'
  GROUP BY 1
),

base AS (
  SELECT
    w.sigla,
    COUNT(DISTINCT u.nm_email) AS qt_base_ativa,
    COUNT(DISTINCT IF(h.nm_email IS NULL, u.nm_email, NULL)) AS qt_base_sem_ht
  FROM win AS w
  JOIN (
    SELECT LOWER(TRIM(u.nm_email)) AS nm_email, s.dt_started_at, s.dt_expires_in
    FROM `bp-datawarehouse.masterdata.dim_subscriptions` AS s
    JOIN `bp-datawarehouse.masterdata.dim_user` AS u ON s.id_user = u.id_user
    WHERE s.nm_type = 'paid' AND u.nm_email IS NOT NULL
      AND (REGEXP_CONTAINS(LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)),
             r'^(bp-)?(good|better|best|black|supporter|mecenas|intermediario|premium|essencial|economico|basico|apoiador|originais|fraterno|patriota|bp-select|combo-liberdade)')
           OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'combo-religioso%'
           OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'combo-essencial%'
           OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'extensao-assinatura-%'
           OR LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) LIKE 'bolsa-mecenas%')
      AND LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) <> 'essencial-estudar-bem'
  ) AS u
    ON DATE(u.dt_started_at) <= w.dt_ini AND DATE(u.dt_expires_in) >= w.dt_ini
  LEFT JOIN (
    SELECT w2.sigla, LOWER(TRIM(c.nm_email)) AS nm_email
    FROM win AS w2
    JOIN `bp-datawarehouse.masterdata.fct_transactions` AS t
      ON DATE(t.dt_ordered_at) < w2.dt_ini AND t.nm_status = 'approved' AND t.vl_payment_gross > 1000
    JOIN `bp-datawarehouse.masterdata.dim_contact` AS c USING (id_gateway_customer)
    WHERE c.nm_email IS NOT NULL
    GROUP BY 1, 2
  ) AS h ON h.sigla = w.sigla AND h.nm_email = u.nm_email
  GROUP BY 1
)

SELECT
  w.ord,
  w.sigla,
  w.nm_campanha,
  w.dt_ini,
  w.dt_fim,
  DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1                        AS qt_dias,
  c.qt_compradores,
  ROUND(c.vl_receita)                                           AS vl_receita,
  ROUND(c.vl_ticket)                                            AS vl_ticket,
  ROUND(c.vl_rec_vitalicio)                                     AS vl_receita_vitalicio,
  -- mídia
  ROUND(m.vl_midia_tag)                                         AS vl_midia,
  ROUND(m.vl_midia_janela)                                      AS vl_midia_janela,
  m.qt_campanhas_midia,
  ROUND(m.vl_midia_tag / NULLIF(c.qt_compradores, 0), 2)        AS vl_cac,
  ROUND(m.vl_midia_tag / NULLIF(c.qt_comp_midia, 0), 2)         AS vl_cac_canal_midia,
  ROUND(c.vl_receita / NULLIF(m.vl_midia_tag, 0), 2)            AS vl_roas,
  ROUND(1000 * m.vl_midia_tag / NULLIF(m.qt_impressoes, 0), 2)  AS vl_cpm,
  ROUND(m.vl_midia_tag / NULLIF(m.qt_cliques, 0), 2)            AS vl_cpc,
  -- mix de canal (compradores)
  ROUND(100 * c.qt_comp_midia     / c.qt_compradores, 1)        AS pct_comp_midia,
  ROUND(100 * c.qt_comp_comercial / c.qt_compradores, 1)        AS pct_comp_comercial,
  ROUND(100 * c.qt_comp_crm       / c.qt_compradores, 1)        AS pct_comp_crm,
  -- mix de canal (receita)
  ROUND(100 * c.vl_rec_midia      / c.vl_receita, 1)            AS pct_rec_midia,
  ROUND(100 * c.vl_rec_comercial  / c.vl_receita, 1)            AS pct_rec_comercial,
  ROUND(100 * c.vl_rec_crm        / c.vl_receita, 1)            AS pct_rec_crm,
  ROUND(100 * c.vl_rec_organico   / c.vl_receita, 1)            AS pct_rec_organico,
  -- status
  ROUND(100 * c.qt_membro     / c.qt_compradores, 1)            AS pct_membro,
  ROUND(100 * c.qt_ex_membro  / c.qt_compradores, 1)            AS pct_ex_membro,
  ROUND(100 * c.qt_nao_membro / c.qt_compradores, 1)            AS pct_nao_membro,
  ROUND(100 * c.qt_primeira_ht / c.qt_compradores, 1)           AS pct_primeira_ht,
  -- esforço
  ROUND(cr.qt_disparos / (DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1)) AS qt_disparos_dia,
  ROUND(cr.vl_receita_crm_janela / NULLIF(cr.qt_disparos / 1000, 0), 2) AS vl_crm_por_1k,
  ROUND(co.qt_abordagens / (DATE_DIFF(w.dt_fim, w.dt_ini, DAY) + 1)) AS qt_abordagens_dia,
  ROUND(100 * co.qt_conversas / NULLIF(co.qt_abordagens, 0), 1)  AS pct_resposta_abordagem,
  -- base
  b.qt_base_ativa,
  ROUND(100 * (b.qt_base_ativa - b.qt_base_sem_ht) / b.qt_base_ativa, 1) AS pct_base_com_ht
FROM win AS w
LEFT JOIN comp      AS c  USING (sigla)
LEFT JOIN midia     AS m  USING (sigla)
LEFT JOIN crm       AS cr USING (sigla)
LEFT JOIN comercial AS co USING (sigla)
LEFT JOIN base      AS b  USING (sigla)
ORDER BY w.ord;
