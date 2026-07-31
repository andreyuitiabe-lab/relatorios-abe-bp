-- Cadastro em campanhas (tags de lead) dos compradores BP10
WITH compras_bp10 AS (
  SELECT
    t.dt_ordered_at,
    t.bl_lifetime_offer,
    t.nm_gateway_plan,
    LOWER(c.nm_email) AS email
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) >= '2026-06-11'
    AND (
      REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_utm_campaign, '')), r'bp10|vit')
      OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_lead_first_tracking, '') || ' ' || COALESCE(t.nm_lead_last_tracking, '')), r'bp10')
      OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_checkout_name, '') || ' ' || COALESCE(t.nm_pptc_tracking_name, '')), r'anos|aniversario|(^|/| )10(/|$)')
    )
),

primeira AS (
  SELECT *
  FROM compras_bp10
  QUALIFY ROW_NUMBER() OVER (PARTITION BY email ORDER BY dt_ordered_at) = 1
),

leads AS (
  SELECT
    LOWER(l.nm_email) AS email,
    l.nm_tag,
    MIN(l.dt_registered_at_br) AS dt_reg
  FROM datamart.dtm_analytics_lead_conversion l
  WHERE LOWER(l.nm_email) IN (SELECT email FROM primeira)
  GROUP BY 1, 2
),

agg AS (
  SELECT
    p.email,
    COUNTIF(l.nm_tag = 'BP10') > 0 AS lead_bp10,
    COUNTIF(l.nm_tag != 'BP10' AND l.dt_reg < p.dt_ordered_at) AS qt_outras_tags_previas,
    ARRAY_AGG(IF(l.nm_tag != 'BP10' AND l.dt_reg < p.dt_ordered_at, l.nm_tag, NULL) IGNORE NULLS) AS outras_tags
  FROM primeira p
  LEFT JOIN leads l USING (email)
  GROUP BY 1
)

SELECT
  COUNT(*) AS compradores,
  COUNTIF(lead_bp10) AS cadastrou_bp10,
  COUNTIF(NOT lead_bp10 AND qt_outras_tags_previas > 0) AS so_outras_campanhas,
  COUNTIF(lead_bp10 AND qt_outras_tags_previas > 0) AS bp10_e_outras,
  COUNTIF(NOT lead_bp10 AND qt_outras_tags_previas = 0) AS nunca_foi_lead,
  ROUND(100 * COUNTIF(lead_bp10) / COUNT(*), 1) AS pct_bp10,
  ROUND(100 * COUNTIF(NOT lead_bp10 AND qt_outras_tags_previas = 0) / COUNT(*), 1) AS pct_nunca_lead
FROM agg
