-- Perfil dos compradores BP10 (atribuição corrigida) por produto
WITH compras_bp10 AS (
  SELECT
    t.id_transaction,
    t.id_gateway_customer,
    t.dt_ordered_at,
    t.vl_payment_gross,
    t.nm_gateway_plan,
    t.nm_plan_label,
    t.bl_lifetime_offer,
    LOWER(c.nm_email) AS email
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) >= '2026-06-11'
    AND (
      REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_utm_campaign, '')), r'bp10|vit')
      OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_lead_first_tracking, '') || ' ' || COALESCE(t.nm_lead_last_tracking, '')), r'bp10')
      -- caminho: 'anos'/'aniversario' em qualquer lugar; '10' só como segmento de caminho (evita tier [10r])
      OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_checkout_name, '') || ' ' || COALESCE(t.nm_pptc_tracking_name, '')), r'anos|aniversario|(^|/| )10(/|$)')
    )
),

-- primeira compra BP10 de cada pessoa (email)
primeira AS (
  SELECT *
  FROM compras_bp10
  QUALIFY ROW_NUMBER() OVER (PARTITION BY email ORDER BY dt_ordered_at) = 1
),

-- todas as contas (id_gateway_customer) associadas aos emails do cohort
contas AS (
  SELECT LOWER(c.nm_email) AS email, c.id_gateway_customer
  FROM masterdata.dim_contact c
  WHERE LOWER(c.nm_email) IN (SELECT email FROM primeira)
),

-- histórico de compras aprovadas ANTES da primeira compra BP10 (qualquer conta do email)
historico AS (
  SELECT
    p.email,
    COUNT(*) AS qt_tx_previas,
    COUNTIF(h.bl_lifetime_offer) AS qt_vitalicio_previo,
    MIN(h.dt_ordered_at) AS dt_primeira_compra_ever
  FROM primeira p
  JOIN contas ct USING (email)
  JOIN masterdata.fct_transactions h
    ON h.id_gateway_customer = ct.id_gateway_customer
    AND h.nm_status = 'approved'
    AND h.dt_ordered_at < p.dt_ordered_at
  GROUP BY 1
),

-- assinatura ativa na data da compra BP10
ativos AS (
  SELECT DISTINCT p.email
  FROM primeira p
  JOIN contas ct USING (email)
  JOIN masterdata.dim_subscriptions s
    ON s.id_gateway_customer = ct.id_gateway_customer
    AND s.nm_status IN ('active', 'wo renewal')
    AND s.nm_type = 'paid'
    AND s.dt_started_at <= p.dt_ordered_at
    AND s.dt_expires_in >= p.dt_ordered_at
),

classificado AS (
  SELECT
    p.email,
    p.vl_payment_gross,
    CASE
      WHEN p.bl_lifetime_offer AND p.nm_gateway_plan = 'black' THEN '1. Vitalício Black'
      WHEN p.bl_lifetime_offer AND p.nm_gateway_plan = 'best' THEN '2. Vitalício Premium'
      WHEN p.bl_lifetime_offer AND p.nm_gateway_plan = 'good' THEN '3. Vitalício Básico'
      WHEN p.bl_lifetime_offer AND p.nm_gateway_plan = 'supporter' THEN '4. Vitalício Apoiador'
      WHEN p.bl_lifetime_offer THEN '5. Vitalício (outros)'
      WHEN p.nm_gateway_plan LIKE 'mecenas%' THEN '6. Mecenas'
      WHEN p.nm_gateway_plan LIKE '%clube-do-livro%' OR p.nm_gateway_plan LIKE 'ebooks%' OR p.nm_gateway_plan = 'analises-clube-livro' THEN '7. Clube do Livro'
      WHEN p.nm_gateway_plan LIKE '%odisseia%' THEN '8. Odisseia'
      WHEN p.nm_gateway_plan = 'best' THEN '9. Assinatura Premium'
      WHEN p.nm_gateway_plan IN ('good', 'better') OR p.nm_gateway_plan LIKE 'bp-essencial%' OR p.nm_gateway_plan LIKE '%extensao-assinatura-good%' THEN '9. Assinatura Essencial/Interm.'
      ELSE '9. Assinatura Apoiador/combos'
    END AS produto,
    CASE
      WHEN h.email IS NULL THEN 'Novo (1a compra)'
      WHEN a.email IS NOT NULL OR h.qt_vitalicio_previo > 0 THEN 'Membro ativo'
      ELSE 'Ex-membro'
    END AS perfil
  FROM primeira p
  LEFT JOIN historico h USING (email)
  LEFT JOIN ativos a USING (email)
)

SELECT
  produto,
  COUNT(*) AS compradores,
  ROUND(SUM(vl_payment_gross)) AS receita,
  COUNTIF(perfil = 'Novo (1a compra)') AS novos,
  COUNTIF(perfil = 'Membro ativo') AS ativos,
  COUNTIF(perfil = 'Ex-membro') AS ex_membros,
  ROUND(100 * COUNTIF(perfil = 'Novo (1a compra)') / COUNT(*), 1) AS pct_novos,
  ROUND(100 * COUNTIF(perfil = 'Membro ativo') / COUNT(*), 1) AS pct_ativos,
  ROUND(100 * COUNTIF(perfil = 'Ex-membro') / COUNT(*), 1) AS pct_ex
FROM classificado
GROUP BY 1
ORDER BY 1
