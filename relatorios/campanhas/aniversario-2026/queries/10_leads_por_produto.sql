-- Origem de cadastro (lead) por grupo de produto — compradores BP10
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
    CASE
      WHEN p.bl_lifetime_offer THEN 'Vitalício'
      WHEN p.nm_gateway_plan LIKE 'mecenas%' THEN 'Mecenas'
      WHEN p.nm_gateway_plan LIKE '%clube-do-livro%' OR p.nm_gateway_plan LIKE 'ebooks%' OR p.nm_gateway_plan = 'analises-clube-livro' THEN 'Clube do Livro'
      WHEN p.nm_gateway_plan LIKE '%odisseia%' THEN 'Odisseia'
      ELSE 'Assinatura'
    END AS produto,
    COUNTIF(l.nm_tag = 'BP10') > 0 AS lead_bp10,
    COUNTIF(l.nm_tag != 'BP10' AND l.dt_reg < p.dt_ordered_at) > 0 AS lead_outras
  FROM primeira p
  LEFT JOIN leads l USING (email)
  GROUP BY 1, 2
)

SELECT
  produto,
  COUNT(*) AS compradores,
  ROUND(100 * COUNTIF(lead_bp10) / COUNT(*), 1) AS pct_lead_bp10,
  ROUND(100 * COUNTIF(NOT lead_bp10 AND lead_outras) / COUNT(*), 1) AS pct_so_outras,
  ROUND(100 * COUNTIF(NOT lead_bp10 AND NOT lead_outras) / COUNT(*), 1) AS pct_nunca_lead
FROM agg
GROUP BY 1
ORDER BY 2 DESC
