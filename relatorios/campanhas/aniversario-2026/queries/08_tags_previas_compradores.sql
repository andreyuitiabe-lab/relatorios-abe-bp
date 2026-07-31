-- Top campanhas em que os compradores BP10 já tinham se cadastrado antes da compra
WITH compras_bp10 AS (
  SELECT
    t.dt_ordered_at,
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
)

SELECT
  l.nm_tag,
  COUNT(DISTINCT p.email) AS compradores,
  ROUND(100 * COUNT(DISTINCT p.email) / 3481, 1) AS pct_cohort
FROM primeira p
JOIN datamart.dtm_analytics_lead_conversion l
  ON LOWER(l.nm_email) = p.email
  AND l.dt_registered_at_br < p.dt_ordered_at
  AND l.nm_tag != 'BP10'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20
