-- Lift univariado por feature: taxa de conversão a Mecenas vs taxa base (0,759%).
-- Universo: 1.607.727 compradores (>=1 tx aprovada). Requer 00_base_qualificacao.sql.
WITH b AS (
  SELECT *,
    CASE WHEN cd_income_decile = -1 OR cd_income_decile IS NULL THEN 'sem CEP'
         WHEN cd_income_decile >= 9 THEN 'decil 9-10'
         WHEN cd_income_decile >= 7 THEN 'decil 7-8'
         WHEN cd_income_decile >= 4 THEN 'decil 4-6'
         ELSE 'decil 1-3' END AS f_renda,
    CASE WHEN nm_credit_card_level_max IS NULL THEN 'sem cartao'
         WHEN nm_credit_card_level_max IN ('6_black', '5_amex') THEN 'black/amex'
         WHEN nm_credit_card_level_max = '4_platinum' THEN 'platinum'
         WHEN nm_credit_card_level_max = '3_gold' THEN 'gold'
         ELSE 'standard/debit' END AS f_cartao,
    CASE WHEN pc_similaridade IS NULL THEN 'sem empresa'
         WHEN pc_similaridade >= 0.95 THEN 'socio @0.95'
         WHEN pc_similaridade >= 0.90 THEN 'socio @0.90'
         WHEN pc_similaridade >= 0.70 THEN 'socio @0.70'
         ELSE 'socio @<0.70' END AS f_cnpj,
    CASE WHEN qt_dias_casa >= 2555 THEN '7+ anos'
         WHEN qt_dias_casa >= 1460 THEN '4-7 anos'
         WHEN qt_dias_casa >= 730 THEN '2-4 anos'
         WHEN qt_dias_casa >= 365 THEN '1-2 anos'
         ELSE '<1 ano' END AS f_casa,
    CASE WHEN vl_total_outras >= 5000 THEN 'gastou 5k+'
         WHEN vl_total_outras >= 2000 THEN 'gastou 2-5k'
         WHEN vl_total_outras >= 500 THEN 'gastou 500-2k'
         WHEN vl_total_outras >= 100 THEN 'gastou 100-500'
         ELSE 'gastou <100' END AS f_gasto,
    CASE WHEN bl_vitalicio = 1 THEN 'vitalicio'
         WHEN bl_black = 1 THEN 'black'
         WHEN bl_certificacao = 1 THEN 'certificacao'
         WHEN bl_cdl = 1 THEN 'clube do livro'
         ELSE 'nenhum high-ticket' END AS f_produto
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`
),

base AS (SELECT COUNT(*) AS bn, COUNTIF(bl_is_mecenas) AS bm FROM b),

u AS (
  SELECT 'renda' AS dim, f_renda AS val, COUNT(*) AS n, COUNTIF(bl_is_mecenas) AS m FROM b GROUP BY 2
  UNION ALL SELECT 'cartao', f_cartao, COUNT(*), COUNTIF(bl_is_mecenas) FROM b GROUP BY 2
  UNION ALL SELECT 'cnpj', f_cnpj, COUNT(*), COUNTIF(bl_is_mecenas) FROM b GROUP BY 2
  UNION ALL SELECT 'tempo_casa', f_casa, COUNT(*), COUNTIF(bl_is_mecenas) FROM b GROUP BY 2
  UNION ALL SELECT 'gasto_previo', f_gasto, COUNT(*), COUNTIF(bl_is_mecenas) FROM b GROUP BY 2
  UNION ALL SELECT 'produto_previo', f_produto, COUNT(*), COUNTIF(bl_is_mecenas) FROM b GROUP BY 2
  UNION ALL SELECT 'genero', COALESCE(nm_gender_inferred, '?'), COUNT(*), COUNTIF(bl_is_mecenas) FROM b GROUP BY 2
)

SELECT
  u.dim,
  u.val,
  u.n AS pessoas,
  u.m AS mecenas,
  ROUND(100 * u.m / u.n, 2) AS pc_conv,
  ROUND((u.m / u.n) / (base.bm / base.bn), 2) AS lift
FROM u
CROSS JOIN base
WHERE u.n >= 200
ORDER BY u.dim, lift DESC
