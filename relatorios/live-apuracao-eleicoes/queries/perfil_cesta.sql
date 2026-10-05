-- Compradores da live (por e-mail): o maior plano que levaram × quem eram antes da compra.
-- Perfil medido 10 min antes da 1ª compra, para não contar a assinatura recém-criada.
WITH tx AS (
  SELECT LOWER(c.nm_email) AS e, t.dt_ordered_at, t.nm_plan_label, t.bl_is_commercial_channel AS com, t.vl_payment_gross AS v
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE AND t.nm_pptc_utm_content = 'apuracao_eleicoes_04out'
),
pessoa AS (
  SELECT e, MIN(dt_ordered_at) AS t0, LOGICAL_OR(com) AS com, SUM(v) AS v,
    CASE
      WHEN LOGICAL_OR(nm_plan_label LIKE '%Vital%' OR nm_plan_label LIKE 'Black%') THEN 'Black / Vitalício'
      WHEN LOGICAL_OR(nm_plan_label LIKE 'Premium%' OR nm_plan_label LIKE '%Premium') THEN 'Premium'
      WHEN LOGICAL_OR(nm_plan_label IN ('Básico', 'Extensao Assinatura Good') OR nm_plan_label LIKE '%Essencial%' OR nm_plan_label LIKE '%Salvador%') THEN 'Essencial'
      WHEN LOGICAL_OR(nm_plan_label = 'Apoiador') THEN 'Apoiador'
      ELSE 'Outros'
    END AS cesta,
    LOGICAL_OR(nm_plan_label LIKE 'Extensao%') AS bump_2ano
  FROM tx GROUP BY 1
),
subs AS (
  SELECT LOWER(c.nm_email) AS e, s.dt_started_at, s.dt_expires_in
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE s.nm_type = 'paid'
),
prev AS (
  SELECT LOWER(c.nm_email) AS e, MIN(t.dt_ordered_at) AS primeira
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
  GROUP BY 1
),
flags AS (
  SELECT p.e,
    LOGICAL_OR(s.dt_started_at < DATETIME_SUB(p.t0, INTERVAL 10 MINUTE) AND s.dt_expires_in >= p.t0) AS ativo,
    LOGICAL_OR(s.dt_started_at < DATETIME_SUB(p.t0, INTERVAL 10 MINUTE)) AS teve_sub
  FROM pessoa p LEFT JOIN subs s USING (e)
  GROUP BY 1
),
perfil AS (
  SELECT p.*,
    CASE
      WHEN f.ativo THEN 'Membro ativo'
      WHEN f.teve_sub THEN 'Ex-membro'
      WHEN r.primeira < DATETIME_SUB(p.t0, INTERVAL 10 MINUTE) THEN 'Já comprou, sem assinatura'
      ELSE 'Novo na base'
    END AS seg
  FROM pessoa p JOIN flags f USING (e) LEFT JOIN prev r USING (e)
)
SELECT seg, cesta, COUNT(*) AS pessoas, COUNTIF(bump_2ano) AS bump_2ano, COUNTIF(com) AS via_comercial, ROUND(SUM(v)) AS receita
FROM perfil
GROUP BY 1, 2
ORDER BY 1, 2
