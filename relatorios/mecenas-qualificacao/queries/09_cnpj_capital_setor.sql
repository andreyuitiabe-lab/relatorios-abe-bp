-- Sócio de empresa: propensão por capital social, nº de empresas e setor (CNAE).
-- Conclusão que a query sustenta: o que discrimina é o PORTE da empresa, não o fato de ser sócio.
WITH b AS (
  SELECT
    bl_is_mecenas,
    vl_total_mecenas,
    CASE WHEN pc_similaridade < 0.95 OR pc_similaridade IS NULL THEN NULL
         WHEN vl_capital_social >= 1000000 THEN 'Capital acima de R$ 1 mi'
         WHEN vl_capital_social >= 100000 THEN 'Capital R$ 100 mil a 1 mi'
         WHEN vl_capital_social >= 10000 THEN 'Capital R$ 10 a 100 mil'
         ELSE 'Capital abaixo de R$ 10 mil' END AS f_cap,
    IF(pc_similaridade >= 0.95, CAST(LEAST(qt_empresas, 4) AS STRING), NULL) AS f_qtd,
    IF(pc_similaridade >= 0.95, (SELECT x FROM UNNEST(arr_cnae_section) x LIMIT 1), NULL) AS f_cnae
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`
),

base AS (
  SELECT COUNT(*) AS bn, COUNTIF(bl_is_mecenas) AS bm
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`
),

u AS (
  SELECT 'capital' AS d, f_cap AS v, COUNT(*) AS n, COUNTIF(bl_is_mecenas) AS m,
    AVG(IF(bl_is_mecenas, vl_total_mecenas, NULL)) AS tk
  FROM b WHERE f_cap IS NOT NULL GROUP BY 2
  UNION ALL
  SELECT 'qtd_empresas', f_qtd, COUNT(*), COUNTIF(bl_is_mecenas),
    AVG(IF(bl_is_mecenas, vl_total_mecenas, NULL))
  FROM b WHERE f_qtd IS NOT NULL GROUP BY 2
  UNION ALL
  SELECT 'cnae', f_cnae, COUNT(*), COUNTIF(bl_is_mecenas),
    AVG(IF(bl_is_mecenas, vl_total_mecenas, NULL))
  FROM b WHERE f_cnae IS NOT NULL GROUP BY 2
)

SELECT
  u.d AS dim,
  u.v AS valor,
  u.n AS pessoas,
  u.m AS mecenas,
  ROUND(100 * u.m / u.n, 2) AS pc_conv,
  ROUND((u.m / u.n) / (base.bm / base.bn), 2) AS lift,
  ROUND(u.tk) AS ticket
FROM u
CROSS JOIN base
WHERE u.n >= 500
ORDER BY u.d, lift DESC
