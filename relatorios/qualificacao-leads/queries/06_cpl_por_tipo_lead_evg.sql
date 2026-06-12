-- CPL por tipo de lead × anúncio — Campanha EVG
-- Método: custo do anúncio dividido igualmente entre todos os leads captados por ele.
-- Distorção: assume que cada lead custou o mesmo dentro do mesmo anúncio.
--   Aceitável para comparar ad sets; dentro do mesmo ad set com audiência mista,
--   é a melhor estimativa disponível sem segmentação por público.
-- Grain de saída: 1 linha por (anúncio × tipo_de_lead)

WITH

-- ── 1. LEADS DA CAMPANHA EVG ─────────────────────────────────────────────────

leads AS (
  SELECT
    nm_email,
    nm_tag,
    dt_registered_at_br,
    -- Extrai id do anúncio do utm_content (padrão BP: sufixo __<id>)
    COALESCE(
      REGEXP_EXTRACT(utm_content, r'__(\d+)$'),
      'sem_id'
    )                                                   AS id_ad,
    nm_lead_channel,
    -- Receita total atribuída a este lead (last-click pela tag)
    (
      SELECT COALESCE(SUM(t.vl_payment_gross), 0)
      FROM UNNEST(arr_st_approved_transactions) AS t
    )                                                   AS receita_total,
    qt_vendas
  FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
  WHERE nm_tag = 'EVG'
),

-- ── 2. CLASSIFICAÇÃO DO LEAD NO MOMENTO DO CADASTRO ──────────────────────────
-- Fornecido pela Bárbara — inner join em subscription_history melhora performance

subscription_history AS (
  SELECT
    u.nm_email,
    s.dt_started_at,
    s.dt_expires_in,
    s.nm_subscription_recurrence
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` AS s
  LEFT JOIN `bp-datawarehouse.masterdata.dim_user` AS u
    ON s.id_user = u.id_user
  INNER JOIN leads ON leads.nm_email = u.nm_email
  WHERE s.nm_type = 'paid'
),

member_classification_at_purchase AS (
  SELECT
    ap.nm_email,
    ap.nm_tag,
    CASE
      WHEN COUNTIF(s.nm_subscription_recurrence = 'vitalício'
             AND s.dt_started_at <= ap.dt_registered_at_br) > 0
        THEN 'Membro Ativo (Vitalício)'
      WHEN COUNTIF(ap.dt_registered_at_br
             BETWEEN s.dt_started_at AND s.dt_expires_in) > 0
        THEN 'Membro Ativo'
      WHEN COUNTIF(s.dt_started_at < ap.dt_registered_at_br) > 0
        THEN 'Ex-Membro'
      ELSE 'Não Membro'
    END AS lead_status_at_registration
  FROM leads AS ap
  LEFT JOIN subscription_history AS s ON ap.nm_email = s.nm_email
  GROUP BY ap.nm_email, ap.nm_tag
),

leads_com_status AS (
  SELECT
    l.*,
    COALESCE(m.lead_status_at_registration, 'Não Membro') AS lead_status
  FROM leads l
  LEFT JOIN member_classification_at_purchase m
    ON l.nm_email = m.nm_email AND l.nm_tag = m.nm_tag
),

-- ── 3. INVESTIMENTO POR ANÚNCIO (META ADS) ───────────────────────────────────

investimento AS (
  SELECT
    CAST(id_advertising AS STRING)                      AS id_ad,
    ANY_VALUE(nm_ad_set_name)                           AS nm_ad_set_name,
    ANY_VALUE(nm_ad_name)                               AS nm_ad_name,
    SUM(vl_amount_spent)                                AS investimento_total
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE DATE(reference_date) BETWEEN '2026-05-21' AND '2026-06-08'
    AND CONTAINS_SUBSTR(nm_campaign_name, '[EVG]')
  GROUP BY 1
),

-- ── 4. TOTAL DE LEADS POR ANÚNCIO (para rateio do custo) ─────────────────────

leads_por_ad AS (
  SELECT
    id_ad,
    COUNT(*)                                            AS total_leads_no_ad
  FROM leads_com_status
  GROUP BY 1
),

-- ── 5. AGREGAÇÃO: anúncio × tipo de lead ─────────────────────────────────────

resultado AS (
  SELECT
    COALESCE(i.nm_ad_set_name, l.id_ad)                AS nm_ad_set,
    COALESCE(i.nm_ad_name, l.id_ad)                    AS nm_ad,
    l.lead_status,

    COUNT(*)                                            AS leads,
    la.total_leads_no_ad,
    ROUND(COUNT(*) / la.total_leads_no_ad * 100, 1)    AS pct_mix,

    -- CPL: custo rateado igualmente entre todos os leads do anúncio
    ROUND(
      COALESCE(i.investimento_total, 0) / NULLIF(la.total_leads_no_ad, 0),
      2
    )                                                   AS cpl_r$,

    COUNTIF(l.qt_vendas > 0)                           AS convertidos,
    ROUND(COUNTIF(l.qt_vendas > 0) / NULLIF(COUNT(*), 0) * 100, 2)
                                                        AS taxa_conv_pct,
    ROUND(SUM(l.receita_total) / NULLIF(COUNT(*), 0), 2)
                                                        AS rpl_r$,

    -- Folga = RPL - CPL (positivo = gera mais do que custa)
    ROUND(
      SUM(l.receita_total) / NULLIF(COUNT(*), 0)
      - COALESCE(i.investimento_total, 0) / NULLIF(la.total_leads_no_ad, 0),
      2
    )                                                   AS folga_r$,

    ROUND(COALESCE(i.investimento_total, 0), 0)        AS investimento_total_r$

  FROM leads_com_status l
  LEFT JOIN leads_por_ad la USING (id_ad)
  LEFT JOIN investimento i USING (id_ad)
  GROUP BY 1, 2, 3, la.total_leads_no_ad, i.investimento_total
)

SELECT *
FROM resultado
-- Mínimo de amostra para estabilidade estatística
WHERE leads >= 30
ORDER BY
  nm_ad_set,
  -- Ordena tipos dentro de cada anúncio por valor gerado
  rpl_r$ DESC;
