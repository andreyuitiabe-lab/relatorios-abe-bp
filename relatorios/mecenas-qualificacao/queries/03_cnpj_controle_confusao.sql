-- "Ser sócio de empresa ajuda?" — teste de confusão.
-- Sócio correlaciona com renda e cartão. O lift sobrevive DENTRO de cada estrato renda x cartão?
-- Resultado (ago/2026): sim, lift 1,26-1,73 nos 16 estratos. Sinal independente, não proxy de riqueza.
WITH b AS (
  SELECT
    bl_is_mecenas,
    IF(pc_similaridade >= 0.95, 'socio', 'nao socio') AS f_cnpj,
    CASE WHEN nm_credit_card_level_max IN ('6_black', '5_amex') THEN 'black/amex'
         WHEN nm_credit_card_level_max = '4_platinum' THEN 'platinum'
         WHEN nm_credit_card_level_max IS NULL THEN 'sem cartao'
         ELSE 'gold-abaixo' END AS f_cartao,
    CASE WHEN cd_income_decile >= 9 THEN 'decil 9-10'
         WHEN cd_income_decile >= 7 THEN 'decil 7-8'
         WHEN cd_income_decile IS NULL OR cd_income_decile = -1 THEN 'sem CEP'
         ELSE 'decil 1-6' END AS f_renda
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`
)

SELECT
  f_cartao,
  f_renda,
  COUNTIF(f_cnpj = 'socio') AS n_socio,
  ROUND(100 * SAFE_DIVIDE(COUNTIF(f_cnpj = 'socio' AND bl_is_mecenas), COUNTIF(f_cnpj = 'socio')), 2) AS conv_socio,
  COUNTIF(f_cnpj = 'nao socio') AS n_nao,
  ROUND(100 * SAFE_DIVIDE(COUNTIF(f_cnpj = 'nao socio' AND bl_is_mecenas), COUNTIF(f_cnpj = 'nao socio')), 2) AS conv_nao,
  ROUND(SAFE_DIVIDE(
    SAFE_DIVIDE(COUNTIF(f_cnpj = 'socio' AND bl_is_mecenas), COUNTIF(f_cnpj = 'socio')),
    SAFE_DIVIDE(COUNTIF(f_cnpj = 'nao socio' AND bl_is_mecenas), COUNTIF(f_cnpj = 'nao socio'))
  ), 2) AS lift_cnpj_dentro_estrato
FROM b
GROUP BY 1, 2
HAVING n_socio >= 300 AND n_nao >= 300
ORDER BY f_cartao, f_renda
