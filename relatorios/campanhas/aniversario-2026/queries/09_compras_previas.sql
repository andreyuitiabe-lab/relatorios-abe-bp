-- O que os compradores BP10 (não-novos) já tinham comprado antes
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
),

contas AS (
  SELECT LOWER(c.nm_email) AS email, c.id_gateway_customer
  FROM masterdata.dim_contact c
  WHERE LOWER(c.nm_email) IN (SELECT email FROM primeira)
)

SELECT
  CASE
    WHEN h.bl_lifetime_offer THEN CONCAT('Vitalício ', COALESCE(h.nm_plan_label, h.nm_gateway_plan))
    ELSE COALESCE(h.nm_plan_label, h.nm_gateway_plan)
  END AS produto_previo,
  COUNT(DISTINCT p.email) AS compradores
FROM primeira p
JOIN contas ct USING (email)
JOIN masterdata.fct_transactions h
  ON h.id_gateway_customer = ct.id_gateway_customer
  AND h.nm_status = 'approved'
  AND h.bl_is_renovation = FALSE
  AND h.dt_ordered_at < p.dt_ordered_at
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20
