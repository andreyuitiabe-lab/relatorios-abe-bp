-- Benchmark de cartao/renda na base de membros ativos, para comparar com os compradores UC
-- Benchmark: nivel de cartao e decil de renda entre membros ativos (base geral) vs compradores UC
WITH membros AS (
  SELECT DISTINCT LOWER(TRIM(c.nm_email)) email, s.id_user
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE s.nm_type='paid' AND s.nm_status IN ('active','wo renewal')
    AND s.dt_started_at <= CURRENT_DATETIME() AND s.dt_expires_in >= CURRENT_DATETIME()
    AND REGEXP_CONTAINS(LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)),
          r'^(bp-)?(good|better|best|black|supporter|mecenas|intermediario|premium|essencial|economico|basico|apoiador|originais|originals|fraterno|combo-religioso|extensao-assinatura|bolsa-mecenas)')
    AND LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)) NOT LIKE '%teller%'
),
cart AS (
  SELECT LOWER(TRIM(nm_email)) email, MAX(nm_credit_card_level_max) nivel
  FROM `bp-datawarehouse.staging.int_credit_card_level` GROUP BY 1
),
rend AS (SELECT id_user, cd_income_decile FROM `bp-datawarehouse.datamart.dtm_purchasing_power`)
SELECT
  'Base membros ativos' grupo,
  COUNT(DISTINCT m.email) n,
  ROUND(100*COUNT(DISTINCT IF(c.nivel IN ('6_black','5_amex','4_platinum'), m.email, NULL))
        /COUNT(DISTINCT IF(c.nivel IS NOT NULL, m.email, NULL)),1) pc_cartao_premium,
  ROUND(100*COUNT(DISTINCT IF(c.nivel='6_black', m.email, NULL))
        /COUNT(DISTINCT IF(c.nivel IS NOT NULL, m.email, NULL)),1) pc_black,
  ROUND(100*COUNT(DISTINCT IF(r.cd_income_decile >= 8, m.email, NULL))
        /COUNT(DISTINCT IF(r.cd_income_decile > 0, m.email, NULL)),1) pc_decil_8mais
FROM membros m
LEFT JOIN cart c USING (email)
LEFT JOIN rend r ON r.id_user = m.id_user
