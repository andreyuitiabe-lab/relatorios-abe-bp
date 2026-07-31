-- v3 CANÔNICA: status do membro NO MOMENTO da compra BP10
-- Padrão de queries-referencia.md §"Classificação de status do membro no momento da compra"
-- Operador `>` (estritamente antes): BP10 vende assinatura no mesmo checkout (cross-sell)
WITH compras_bp10 AS (
  SELECT
    t.id_transaction,
    t.dt_ordered_at,
    t.vl_payment_gross,
    t.nm_gateway_plan,
    t.bl_lifetime_offer,
    LOWER(c.nm_email) AS nm_email
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

-- 1ª compra BP10 por pessoa
primeira AS (
  SELECT *
  FROM compras_bp10
  QUALIFY ROW_NUMBER() OVER (PARTITION BY nm_email ORDER BY dt_ordered_at) = 1
),

subscription_history AS (
  SELECT
    LOWER(u.nm_email) AS nm_email,
    s.dt_started_at,
    s.dt_expires_in,
    s.nm_subscription_recurrence
  FROM masterdata.dim_subscriptions AS s
  LEFT JOIN masterdata.dim_user AS u ON s.id_user = u.id_user
  WHERE s.nm_type = 'paid'
    AND LOWER(u.nm_email) IN (SELECT nm_email FROM primeira)
),

member_classification AS (
  SELECT
    p.nm_email,
    ANY_VALUE(p.nm_gateway_plan) AS nm_gateway_plan,
    ANY_VALUE(p.bl_lifetime_offer) AS bl_lifetime_offer,
    CASE
      WHEN COUNTIF(s.nm_subscription_recurrence = 'vitalício' AND s.dt_started_at < p.dt_ordered_at) > 0
        THEN '2. Membro Ativo (Vitalício)'
      WHEN COUNTIF(p.dt_ordered_at > s.dt_started_at AND p.dt_ordered_at <= s.dt_expires_in) > 0
        THEN '1. Membro Ativo'
      WHEN COUNTIF(s.dt_started_at < p.dt_ordered_at) > 0
        THEN '3. Ex-Membro'
      ELSE '4. Não era Membro'
    END AS status_na_compra
  FROM primeira AS p
  LEFT JOIN subscription_history AS s ON p.nm_email = s.nm_email
  GROUP BY p.nm_email, p.dt_ordered_at
)

SELECT
  CASE
    WHEN bl_lifetime_offer THEN 'Vitalício'
    WHEN nm_gateway_plan LIKE 'mecenas%' THEN 'Mecenas'
    WHEN nm_gateway_plan LIKE '%clube-do-livro%' OR nm_gateway_plan LIKE 'ebooks%' OR nm_gateway_plan = 'analises-clube-livro' THEN 'Clube do Livro'
    WHEN nm_gateway_plan LIKE '%odisseia%' THEN 'Odisseia'
    ELSE 'Assinatura'
  END AS produto,
  COUNT(*) AS compradores,
  COUNTIF(status_na_compra = '1. Membro Ativo') AS ativo,
  COUNTIF(status_na_compra = '2. Membro Ativo (Vitalício)') AS ativo_vit,
  COUNTIF(status_na_compra = '3. Ex-Membro') AS ex_membro,
  COUNTIF(status_na_compra = '4. Não era Membro') AS nao_era,
  ROUND(100 * COUNTIF(status_na_compra LIKE '%Ativo%') / COUNT(*), 1) AS pct_ativo,
  ROUND(100 * COUNTIF(status_na_compra = '3. Ex-Membro') / COUNT(*), 1) AS pct_ex,
  ROUND(100 * COUNTIF(status_na_compra = '4. Não era Membro') / COUNT(*), 1) AS pct_nao_era
FROM member_classification
GROUP BY 1
ORDER BY 2 DESC
